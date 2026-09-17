# Copyright 2025 PhonePe Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import threading
from time import time

from phonepe.sdk.pg.common.configs.credential_config import CredentialConfig
from phonepe.sdk.pg.common.configs.http_client_config import HttpClientConfig
from phonepe.sdk.pg.common.constants.headers import (
    ACCEPT,
    CONTENT_TYPE,
    APPLICATION_JSON,
    X_WWW_FORM_URLENCODED,
)
from phonepe.sdk.pg.common.events.event_builder import (
    build_init_client_event,
    build_oauth_event_none_cached_token,
    build_oauth_event_used_cached_token_failed,
)
from phonepe.sdk.pg.common.events.models.enums.event_type import EventType
from phonepe.sdk.pg.common.events.publisher.event_publisher import EventPublisher
from phonepe.sdk.pg.common.exceptions import ClientError, TooManyRequests
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType
from phonepe.sdk.pg.common.token_handler.oauth_response import OauthResponse
from phonepe.sdk.pg.common.token_handler.token_constants import (
    OAUTH_GRANT_TYPE,
    OAUTH_ENDPOINT,
)
from phonepe.sdk.pg.env import Env, get_oauth_base_url

# Sentinel for "no previous token to compare against" (distinct from None, which is itself a
# valid cached_token_data value).
_NO_PREVIOUS_TOKEN = object()


class TokenService:
    """Token management.

    Fetches a token eagerly at construction, then proactively refreshes it in a background
    thread at half its lifetime, retrying on failure until the token's hard expiry (and, as a
    last-resort safety net, indefinitely with capped backoff beyond that too, since giving up
    permanently would otherwise strand the client with no other way to recover). A lock ensures
    only one fetch/refresh can mutate the cached token at a time, whether it comes from the
    initial construction-time fetch, the proactive background refresh, or a reactive
    force_refresh_token() (triggered when a request gets a 401).

    The initial fetch makes exactly one synchronous attempt on the constructing thread - no
    sleep-based retry blocks the caller. A genuine client-side error (bad credentials, malformed
    request, etc.) fails fast and propagates out of __init__, since retrying identical input
    would fail identically. Any other (transient) failure - connection errors, timeouts, 5xx,
    429 - is handed off to the background thread instead: construction still returns immediately
    without raising, and the background thread keeps retrying with backoff until it succeeds.

    get_auth_token() also keeps its own synchronous lazy-fetch-with-cached-fallback logic as an
    additional safety net beneath the proactive mechanism, for the rare case a real request needs
    a token before/despite the background refresh succeeding.
    """

    # Floor on how soon the background loop is allowed to attempt another proactive refresh,
    # even if the cached token's half-life computes to "now" or earlier (e.g. a token whose
    # issued_at/expires_at are already stale by the time it's cached). Without this floor, such
    # a token would cause the loop to busy-refresh with no pacing at all.
    MIN_SECONDS_BETWEEN_PROACTIVE_ATTEMPTS = 1.0

    # Ceiling on how long the background loop will ever sleep in one go. Without this cap, a
    # malformed/unexpected token response (e.g. timestamps in the wrong unit, or otherwise huge)
    # could compute a sleep duration that overflows the OS-level timer used by threading.Event's
    # timed wait (raising OverflowError and crashing the thread) - re-checking at least this
    # often also means force_refresh_token()/close() are never blocked for unreasonably long.
    MAX_SECONDS_BETWEEN_PROACTIVE_ATTEMPTS = 24 * 60 * 60  # 1 day

    PROACTIVE_REFRESH_BASE_RETRY_DELAY_SECONDS = 1
    PROACTIVE_REFRESH_MAX_RETRY_DELAY_SECONDS = 30  # cap on backoff once past a few attempts

    def __init__(
        self,
        credential_config: CredentialConfig,
        env: Env,
        event_publisher: EventPublisher,
        http_client_config: HttpClientConfig,
    ) -> None:
        self._credential_config = credential_config
        self.event_publisher = event_publisher
        self.event_publisher.send(
            build_init_client_event(event_name=EventType.TOKEN_SERVICE_INITIALIZED)
        )
        self.cached_token_data = None
        self._token_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._background_thread = None
        # the owner (BaseClient) has a reference to close(). All I/O happens in start().
        self._http_command = BaseHttpCommand(host_url=get_oauth_base_url(env),
                                             http_client_config=http_client_config)

    def start(self):
        """Performs the one eager token fetch and starts the proactive refresh thread.
        Kept out of __init__ so the owner can register this instance for cleanup first and
        close() it if this raises."""
        # Exactly one synchronous attempt, with NO sleep-based retry on this (the calling)
        # thread. A genuine client-side error fails fast and propagates. Any transient failure
        # is logged and left to the background thread - started below - to retry with backoff.
        self._fetch_initial_token_or_defer_to_background()

        # Started regardless of whether the fetch above succeeded: if a token was obtained this
        # proactively refreshes it at half-life; if not (transient failure), it takes over
        # retrying immediately.
        self._background_thread = threading.Thread(
            target=self._background_refresh_loop, name="PhonePeTokenRefresher", daemon=True,
        )
        self._background_thread.start()

    def get_current_time(self):
        return int(time())

    def _is_cached_token_valid(self):
        """Checks if token has expired"""
        if self.cached_token_data is None:
            return False

        issued_at = self.cached_token_data.issued_at
        expires_at = self.cached_token_data.expires_at
        current_time = self.get_current_time()

        token_sdk_expiry_time = issued_at + int((expires_at - issued_at) // 2)
        return current_time < token_sdk_expiry_time

    def get_auth_token(self):
        if self._is_cached_token_valid():
            return self._format_token(self.cached_token_data)
        try:
            # Snapshot cached token before fetching, so a concurrent thread that already
            # refreshed it can be detected (avoids a thundering herd of redundant fetches).
            self._fetch_and_store_token(previous_token_data=self.cached_token_data)
        except Exception as exception:
            if self.cached_token_data is None:
                self.event_publisher.send(
                    build_oauth_event_none_cached_token(
                        fetch_attempt_time=self.get_current_time(),
                        api_path=OAUTH_ENDPOINT,
                        exception=exception,
                    )
                )
                logging.error(
                    f"No cached token, error occurred while fetching new token | "
                    f"exception_type={type(exception).__name__} | "
                    f"exception={exception} | "
                    f"cause={getattr(exception, '__cause__', None)} | "
                    f"url={self._http_command._host_url}{OAUTH_ENDPOINT} | "
                    f"connect_timeout={self._http_command._http_client_config.connect_timeout_seconds}s | "
                    f"read_timeout={self._http_command._http_client_config.read_timeout_seconds}s"
                )
                raise exception
            self.event_publisher.send(
                build_oauth_event_used_cached_token_failed(
                    cached_token_issued_at=self.cached_token_data.issued_at,
                    cached_token_expires_at=self.cached_token_data.expires_at,
                    fetch_attempt_time=self.get_current_time(),
                    api_path=OAUTH_ENDPOINT,
                    exception=exception,
                )
            )
            logging.info(
                f"Returning cached token, error occurred while fetching new token | "
                f"exception_type={type(exception).__name__} | "
                f"exception={exception} | "
                f"cause={getattr(exception, '__cause__', None)} | "
                f"url={self._http_command._host_url}{OAUTH_ENDPOINT} | "
                f"connect_timeout={self._http_command._http_client_config.connect_timeout_seconds}s | "
                f"read_timeout={self._http_command._http_client_config.read_timeout_seconds}s"
            )

        # always return cached token, even if auth-client throws exception
        return self._format_token(self.cached_token_data)

    @staticmethod
    def _format_token(token_data):
        return token_data.token_type + " " + token_data.access_token

    def close(self):
        """Stops the proactive background refresh thread and releases pooled HTTP connections
        held by this token service. Safe to call multiple times."""
        self._stop_event.set()
        self._wake_event.set()  # wake the loop immediately instead of waiting out a long sleep
        if self._background_thread is not None and self._background_thread.is_alive():
            self._background_thread.join(timeout=5)
        self._http_command.close()

    def force_refresh_token(self):
        logging.info("Force refreshing token")
        # Not based on _is_cached_token_valid(): a token can still look valid by half-life math
        # yet be the exact one the server just rejected with a 401, so this must always attempt
        # a fetch unless another caller already replaced it (thundering-herd guard).
        self._fetch_and_store_token(previous_token_data=self.cached_token_data)
        # Nudge the background loop to recompute its next-refresh target off the token we just
        # fetched, instead of possibly sleeping on a schedule based on the now-replaced token.
        self._wake_event.set()

    def _fetch_and_store_token(self, previous_token_data=_NO_PREVIOUS_TOKEN):
        """Fetches a fresh token and atomically stores it. Guarded by _token_lock so the eager
        construction-time fetch, the proactive background refresh, the reactive
        force_refresh_token() (401 path), and get_auth_token()'s lazy fallback can never race and
        corrupt/interleave cached_token_data.

        `previous_token_data`, when given, is the `cached_token_data` the caller observed before
        deciding a fetch was needed. If another thread already replaced it by the time this
        caller acquires the lock, the fetch is skipped (thundering-herd guard). Omit it for an
        unconditional fetch (e.g. the very first fetch at construction).

        Returns True if a network fetch happened, False if skipped.
        """
        with self._token_lock:
            if previous_token_data is not _NO_PREVIOUS_TOKEN and self.cached_token_data is not previous_token_data:
                return False
            token_data = self.fetch_token_from_phonepe().json()
            self.cached_token_data = OauthResponse.from_dict(token_data)
            return True

    def _fetch_initial_token_or_defer_to_background(self):
        try:
            self._fetch_and_store_token()
        except ClientError as exception:
            if not isinstance(exception, TooManyRequests):
                # Genuine client-side error (bad credentials, malformed request, etc.) -
                # retrying with the same input would fail identically, so fail fast here instead
                # of silently retrying forever in the background with no way to surface it.
                logging.error(
                    f"Initial token fetch failed with a non-retryable client error, not retrying | "
                    f"exception_type={type(exception).__name__} | exception={exception}"
                )
                self._publish_none_cached_token_event(exception)
                raise
            self._log_initial_fetch_deferred(exception)
        except Exception as exception:
            self._log_initial_fetch_deferred(exception)

    def _log_initial_fetch_deferred(self, exception):
        logging.warning(
            f"Initial token fetch failed with a transient error - construction is NOT blocked "
            f"on retrying it; the background refresh thread will keep retrying instead | "
            f"exception_type={type(exception).__name__} | exception={exception}"
        )

    def _publish_none_cached_token_event(self, exception):
        self.event_publisher.send(
            build_oauth_event_none_cached_token(
                fetch_attempt_time=self.get_current_time(),
                api_path=OAUTH_ENDPOINT,
                exception=exception,
            )
        )

    def _seconds_until_next_refresh(self):
        """Seconds to sleep before the next proactive refresh attempt, based on the currently
        cached token's half-life - floored at MIN_SECONDS_BETWEEN_PROACTIVE_ATTEMPTS so the loop
        can never busy-spin with zero pacing, even if the cached token's timestamps are already
        stale (e.g. clock skew, or a token issued already past its own half-life), and capped at
        MAX_SECONDS_BETWEEN_PROACTIVE_ATTEMPTS to guard against a malformed/unexpected token
        response producing a sleep duration too large for the OS-level timer to handle."""
        if self.cached_token_data is None:
            # No token yet (either this is the very first attempt, or the synchronous fetch in
            # __init__ failed transiently and deferred here) - try again immediately rather than
            # waiting out the usual pacing floor, since there's nothing to lose and a real
            # request may be blocked waiting on get_auth_token()'s own fallback in the meantime.
            return 0.0
        issued_at = self.cached_token_data.issued_at
        expires_at = self.cached_token_data.expires_at
        half_life_at = issued_at + (expires_at - issued_at) / 2
        seconds_until = half_life_at - self.get_current_time()
        return min(
            self.MAX_SECONDS_BETWEEN_PROACTIVE_ATTEMPTS,
            max(self.MIN_SECONDS_BETWEEN_PROACTIVE_ATTEMPTS, seconds_until),
        )

    def _background_refresh_loop(self):
        while not self._stop_event.is_set():
            try:
                sleep_seconds = self._seconds_until_next_refresh()
                woke_early = self._wake_event.wait(timeout=sleep_seconds)
                self._wake_event.clear()
                if self._stop_event.is_set():
                    break
                if woke_early:
                    # Something else (e.g. force_refresh_token on a 401) already updated the
                    # token out of band; just recompute the next sleep target off the fresh data
                    # rather than also refreshing here.
                    continue
                self._proactive_refresh_with_retry_until_expiry()
            except Exception:
                # Defensive: never let an unexpected error (e.g. malformed cached_token_data)
                # silently kill this daemon thread. Log it, pace with the same floor as other
                # attempts, and keep the loop alive.
                logging.exception("Unexpected error in proactive token refresh loop")
                self._stop_event.wait(timeout=self.MIN_SECONDS_BETWEEN_PROACTIVE_ATTEMPTS)

    def _proactive_refresh_with_retry_until_expiry(self):
        attempt = 0
        while not self._stop_event.is_set():
            if self._is_cached_token_valid():
                # Another path already refreshed the token while we were about to retry.
                return
            attempt += 1
            try:
                fetched = self._fetch_and_store_token(previous_token_data=self.cached_token_data)
                if fetched:
                    logging.info(f"Proactive background token refresh succeeded on attempt {attempt}")
                else:
                    # A concurrent force_refresh_token() already replaced the token first.
                    logging.info(
                        "Proactive background token refresh skipped on attempt "
                        f"{attempt}: token was already refreshed by another path"
                    )
                return
            except Exception as exception:
                cached = self.cached_token_data
                if cached is not None:
                    self.event_publisher.send(
                        build_oauth_event_used_cached_token_failed(
                            cached_token_issued_at=cached.issued_at,
                            cached_token_expires_at=cached.expires_at,
                            fetch_attempt_time=self.get_current_time(),
                            api_path=OAUTH_ENDPOINT,
                            exception=exception,
                        )
                    )
                past_expiry = cached is not None and self.get_current_time() >= cached.expires_at
                logging.warning(
                    f"Proactive background token refresh attempt {attempt} failed "
                    f"({'past' if past_expiry else 'before'} hard expiry) | "
                    f"exception_type={type(exception).__name__} | exception={exception}"
                )
                delay = min(
                    self.PROACTIVE_REFRESH_BASE_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)),
                    self.PROACTIVE_REFRESH_MAX_RETRY_DELAY_SECONDS,
                )
                # Keep retrying at least until the cached token's hard expiry, and indefinitely
                # (capped backoff) beyond that too - giving up permanently would otherwise strand
                # the client with no other way to recover. get_auth_token()'s synchronous lazy
                # fallback remains available as an independent safety net for in-flight requests
                # in the meantime. self._stop_event.wait() makes this backoff sleep immediately
                # interruptible by close().
                if self._stop_event.wait(timeout=delay):
                    return

    def fetch_token_from_phonepe(self):
        start = time()
        try:
            response = self._http_command.request(
                method=HttpMethodType.POST,
                url=OAUTH_ENDPOINT,
                data=self._prepare_oauth_body(),
                headers=self._prepare_oauth_headers(),
            )
            logging.info(f"Token fetch succeeded in {time() - start:.3f}s | status={response.status_code}")
            return response
        except Exception as e:
            logging.error(
                f"Token fetch failed after {time() - start:.3f}s | "
                f"exception_type={type(e).__name__} | "
                f"cause={getattr(e, '__cause__', None)}"
            )
            raise

    def _prepare_oauth_headers(self):
        return {CONTENT_TYPE: X_WWW_FORM_URLENCODED, ACCEPT: APPLICATION_JSON}

    def _prepare_oauth_body(self):
        return {
            "client_id": self._credential_config.client_id,
            "client_secret": self._credential_config.client_secret,
            "grant_type": OAUTH_GRANT_TYPE,
            "client_version": self._credential_config.client_version,
        }
