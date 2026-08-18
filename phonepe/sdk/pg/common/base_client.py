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

import json
import logging
import threading
from dataclasses import dataclass

import phonepe
from phonepe.sdk.pg.common.configs.credential_config import CredentialConfig
from phonepe.sdk.pg.common.configs.http_client_config import HttpClientConfig
from phonepe.sdk.pg.common.constants.headers import (
    SOURCE,
    SOURCE_VERSION,
    SOURCE_PLATFORM,
    SOURCE_PLATFORM_VERSION,
    AUTHORIZATION,
    CONTENT_TYPE,
    ACCEPT,
    APPLICATION_JSON,
    SDK_TYPE,
    API_VERSION,
    INTEGRATION,
)
from phonepe.sdk.pg.common.events.publisher.event_publisher_factory import (
    EventPublisherFactory,
)
from phonepe.sdk.pg.common.exceptions import UnauthorizedAccess
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType
from phonepe.sdk.pg.common.token_handler.token_service import TokenService
from phonepe.sdk.pg.common.utils.dict_utils import merge_dict
from phonepe.sdk.pg.env import Env, get_pg_base_url, get_event_ingestion_base_url, get_pci_pg_base_url


class BaseClient:

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        client_version: int,
        env: Env,
        should_publish_events: bool = True,
        http_client_config: HttpClientConfig = None,
    ):
        self.env = env
        self.credential_config = CredentialConfig(
            client_id=client_id,
            client_secret=client_secret,
            client_version=client_version,
        )
        # Same HttpClientConfig applies to every host this client instance talks to (main pg,
        # PCI, event ingestion, oauth) - one merchant traffic profile, consistently tuned.
        self.http_client_config = http_client_config or HttpClientConfig()
        self.should_publish_events = should_publish_events

        # Track resources that need cleanup if a later step fails (e.g. TokenService's eager
        # fetch raising on bad credentials) - otherwise components created earlier (each starts
        # its own background thread) would leak since this partially-built instance is never
        # returned to the caller and close() can never be called on it.
        closables = []
        try:
            self._http_command = BaseHttpCommand(get_pg_base_url(self.env),
                                                 http_client_config=self.http_client_config)
            closables.append(self._http_command)

            self._pci_http_command = BaseHttpCommand(get_pci_pg_base_url(self.env),
                                                     http_client_config=self.http_client_config)
            closables.append(self._pci_http_command)

            self._event_publisher_factory = EventPublisherFactory(
                event_sender=BaseHttpCommand(host_url=get_event_ingestion_base_url(env),
                                             http_client_config=self.http_client_config)
            )
            closables.append(self._event_publisher_factory.event_sender)

            self.event_publisher = self._event_publisher_factory.get_event_publisher(
                should_publish_events=should_publish_events
            )
            closables.append(self.event_publisher)

            self._token_service = TokenService(
                credential_config=self.credential_config,
                env=self.env,
                event_publisher=self.event_publisher,
                http_client_config=self.http_client_config,
            )
            closables.append(self._token_service)

            self.event_publisher.start_publishing_events(
                auth_token_supplier=self._token_service.get_auth_token
            )
        except Exception:
            for closable in reversed(closables):
                try:
                    closable.close()
                except Exception:
                    logging.exception(
                        "Error while releasing a resource during cleanup of a failed client construction"
                    )
            raise

    @classmethod
    def _get_key_lock(cls, cache_key):
        """Returns (creating if necessary) a lock scoped to this one cache_key, so building/
        closing one merchant's client never blocks an unrelated merchant's get_instance()/
        close() call on the same class. `cls._instance_lock` here only guards this tiny
        dict-of-locks bookkeeping - it is held only briefly and NEVER across the actual
        (potentially slow, network-bound) client construction/OAuth fetch or close() below."""
        with cls._instance_lock:
            key_lock = cls._key_locks.get(cache_key)
            if key_lock is None:
                key_lock = threading.Lock()
                cls._key_locks[cache_key] = key_lock
            return key_lock

    @classmethod
    def _get_or_build_cached_instance(cls, cache_key, build_and_register):
        """Thread-safe get-or-create for a subclass's get_instance() singleton cache
        (cls._cached_instances, keyed by cache_key). Checks the cache lock-free first (the
        common hit path), then re-checks under a lock SCOPED TO THIS cache_key before building -
        otherwise two concurrent first-callers for the same key could each build and orphan a
        full duplicate client (threads, pools, and a wasted OAuth fetch), with only one
        surviving in the cache. Using a per-key lock (rather than one shared class-wide lock)
        means a slow/hanging build for one merchant's credentials never blocks get_instance()/
        close() calls for any OTHER merchant's cache_key.

        `build_and_register` is called (with the per-key lock held) only on a genuine cache
        miss; it must construct the new instance, store it in cls._cached_instances[cache_key],
        and return it.
        """
        cached = cls._cached_instances.get(cache_key)
        if cached is not None:
            return cached
        with cls._get_key_lock(cache_key):
            cached = cls._cached_instances.get(cache_key)
            if cached is not None:
                return cached
            return build_and_register()

    def _request_with_token_invalidation(
        self,
        method: HttpMethodType,
        url: str,
        response_obj: dataclass,
        headers: dict = {},
        path_params: dict = None,
        data: dict = None,
        http_command: "BaseHttpCommand" = None,
    ):
        # On UnauthorizedAccess the token cache is invalidated so the next call fetches a fresh
        # token. This method does NOT retry the request itself.
        command = http_command if http_command is not None else self._http_command
        try:
            response_data = command.request(
                method=method,
                url=url,
                headers=merge_dict(self._prepare_headers(), headers),
                path_params=path_params,
                data=data,
            )
        except UnauthorizedAccess as exception:
            logging.info(f"Failed to authorize")
            self._token_service.force_refresh_token()
            raise exception
        if response_obj is None:
            if response_data is not None:
                response_data_json = json.dumps(response_data, default=str)
                logging.info(f"Received a non-empty Response: {response_data_json}")
            return None
        return response_obj.from_dict(response_data.json())

    def close(self):
        """Releases resources held by this client instance: pooled HTTP connections, the event
        publisher's background scheduler, and the token service's background refresh thread.
        Also evicts this instance from its class's get_instance() cache (if present), so a
        later get_instance() call with the same arguments builds a fresh client instead of
        returning this now-closed one. Safe to call multiple times."""
        # The event publisher is stopped before the session it publishes through, otherwise an
        # in-flight flush would re-create pooled connections on an already-closed sender.
        # Each step is isolated so one failure can't leave the remaining components running.
        for closer in (
            self._evict_from_instance_cache,
            self.event_publisher.close,
            self._event_publisher_factory.event_sender.close,
            self._http_command.close,
            self._pci_http_command.close,
            self._token_service.close,
        ):
            try:
                closer()
            except Exception:
                logging.exception("Error while releasing a resource during client close()")

    def _evict_from_instance_cache(self):
        cache_key = getattr(self, "_cache_key", None)
        cached_instances = getattr(type(self), "_cached_instances", None)
        if cache_key is None or cached_instances is None:
            return
        with type(self)._get_key_lock(cache_key):
            if cached_instances.get(cache_key) is self:
                del cached_instances[cache_key]

    def _prepare_headers(self):
        return {
            SOURCE: INTEGRATION,
            SOURCE_VERSION: API_VERSION,
            SOURCE_PLATFORM: SDK_TYPE,
            SOURCE_PLATFORM_VERSION: phonepe.__version__,
            AUTHORIZATION: self._token_service.get_auth_token(),
            CONTENT_TYPE: APPLICATION_JSON,
            ACCEPT: APPLICATION_JSON,
        }
