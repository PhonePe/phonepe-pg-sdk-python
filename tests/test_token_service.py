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

import time as time_module
from time import time
from unittest import TestCase
from unittest.mock import patch

import responses

from phonepe.sdk.pg.common.configs.credential_config import CredentialConfig
from phonepe.sdk.pg.common.events.publisher.event_publisher import EventPublisher
from phonepe.sdk.pg.common.exceptions import PhonePeException, UnauthorizedAccess
from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.common.token_handler.token_service import TokenService
from phonepe.sdk.pg.env import Env, get_oauth_base_url
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient


def _token_json(issued_at, expires_at, access_token="access_token"):
    return {
        "access_token": access_token,
        "encrypted_access_token": "encrypted_access_token",
        "refresh_token": "d0e89cb1-2b3b-41b8-87d9-31411c60edb7",
        "expires_in": expires_at - issued_at,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "session_expires_at": expires_at,
        "token_type": "O-Bearer",
    }


def _add_oauth_mock(status=200, json_body=None):
    responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=status,
                  json=json_body if json_body is not None else _token_json(int(time()), int(time()) + 5014))


class TestTokenService(TestCase):
    """TokenService now fetches its token eagerly at construction (retried on failure), then
    proactively refreshes it in a background thread at half-life. get_auth_token() keeps its own
    synchronous lazy-fetch-with-cached-fallback logic as an additional safety net. Every test here
    that constructs a TokenService must have its OAuth mock registered BEFORE construction, since
    construction itself now makes the first HTTP call (rather than deferring it to the first
    get_auth_token() call, as it did previously).

    Every directly-constructed TokenService (as opposed to a get_instance()-cached singleton
    client) registers its close() via addCleanup immediately after construction, guaranteeing its
    background thread is stopped even if an assertion fails - otherwise a leftover daemon thread
    could keep polling in the background and pollute a LATER test's responses.calls count (since
    responses patches HTTP sending process-wide, not just for the thread/test that set it up)."""

    @responses.activate
    def test_fetch_token(self):
        _add_oauth_mock()
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        self.addCleanup(token_service.close)
        assert len(responses.calls) == 1  # eager fetch at construction, not on first get_auth_token()
        # Compare against a value derived from the same fixture data (not a hardcoded literal),
        # since token-shaped strings get redacted in tool/terminal output and must never be
        # copied by hand from displayed output into test source.
        assert token_service.get_auth_token() == "O-Bearer" + " " + "access_token"
        assert len(responses.calls) == 1  # cached token reused, no extra call

    @responses.activate
    def test_token_refresh_when_immediately_expired(self):
        # issued_at=0 makes the half-life instantly in the past relative to real "now"
        _add_oauth_mock(json_body=_token_json(0, 1709630316))
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        self.addCleanup(token_service.close)
        assert len(responses.calls) == 1  # eager fetch at construction

        _add_oauth_mock(json_body=_token_json(0, 1709630316))
        token_service.get_auth_token()  # notices the (already expired) token is invalid, refetches
        assert len(responses.calls) == 2

    @responses.activate
    def test_token_use_cached(self):
        cur_time = int(time())
        two_sec_more_cur = cur_time + 2
        _add_oauth_mock(json_body=_token_json(cur_time, two_sec_more_cur))

        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        self.addCleanup(token_service.close)

        token_service.get_auth_token()
        token_service.get_auth_token()
        token_service.get_auth_token()

        assert len(responses.calls) == 1  # eager fetch at construction; still valid, no refetch

        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 1)):
            token_service.get_auth_token()  # tries to fetch new token
            token_service.get_auth_token()  # tries to fetch new token
            token_service.get_auth_token()  # tries to fetch new token

        assert len(responses.calls) == 4

    @responses.activate
    def test_token_use_cached_then_cached_valid2(self):
        cur_time = int(time())
        four_sec_more = cur_time + 4
        ten_sec_more = cur_time + 10

        _add_oauth_mock(json_body=_token_json(cur_time, four_sec_more))

        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        self.addCleanup(token_service.close)

        token_service.get_auth_token()
        token_service.get_auth_token()
        token_service.get_auth_token()

        assert len(responses.calls) == 1  # eager fetch at construction

        _add_oauth_mock(json_body=_token_json(cur_time, ten_sec_more))

        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 1)):
            token_service.get_auth_token()  # does not fetch, uses old token
        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 2)):
            token_service.get_auth_token()  # fetches new token
        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 3)):
            token_service.get_auth_token()  # uses old token
        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 4)):
            token_service.get_auth_token()  # uses old token
        assert len(responses.calls) == 2

    @responses.activate
    def test_construction_fails_with_no_cached_token_on_bad_request(self):
        # e.g. invalid client_id/client_secret - retrying with the same credentials would always
        # fail, so this fails fast (no retries) and client construction raises immediately.
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=400,
                      json={"code": "INVALID_CLIENT", "errorCode": "OIM000",
                            "message": "Bad Request: Invalid Client, trackingId: 2123d",
                            "context": {"error_description": "Client authentication failure"}})

        self.assertRaises(PhonePeException, TokenService,
                          credential_config=CredentialConfig(client_id="client_id", client_version=1,
                                                             client_secret="client_secret"),
                          env=Env.SANDBOX, event_publisher=EventPublisher())
        assert len(responses.calls) == 1  # fails fast, no retries for a genuine client error

    @responses.activate
    def test_construction_fails_with_no_cached_token_on_unauthorized(self):
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=401,
                      json={"success": False, "code": "401"})

        self.assertRaises(UnauthorizedAccess, TokenService,
                          credential_config=CredentialConfig(client_id="client_id", client_version=1,
                                                             client_secret="client_secret"),
                          env=Env.SANDBOX, event_publisher=EventPublisher())
        assert len(responses.calls) == 1  # fails fast, no retries for invalid credentials

    def test_construction_does_not_block_on_transient_failure(self):
        # Guards the core behavior change: construction must never sleep/block the calling
        # thread retrying a transient failure - it makes exactly one synchronous attempt, then
        # defers all further retries to the background thread.
        import inspect
        source = inspect.getsource(TokenService._fetch_initial_token_or_defer_to_background)
        assert "sleep" not in source

    @responses.activate
    def test_construction_returns_immediately_and_defers_transient_failure_to_background(self):
        cur = int(time())
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=500)
        _add_oauth_mock(json_body=_token_json(cur, cur + 5014, access_token="recovered_token"))

        start = time()
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id", client_version=1,
                                                                        client_secret="client_secret"),
                                     env=Env.SANDBOX, event_publisher=EventPublisher())
        self.addCleanup(token_service.close)
        elapsed = time() - start

        assert elapsed < 0.5, f"construction blocked for {elapsed:.3f}s on a transient failure"
        assert token_service.cached_token_data is None  # not yet - first attempt failed, no retry here
        assert len(responses.calls) == 1  # exactly one synchronous attempt, no sleep-retry loop

        # Background thread retries immediately (no pacing floor while there's no token yet) and
        # recovers using the second registered mock.
        deadline = time() + 2
        while token_service.cached_token_data is None and time() < deadline:
            pass
        assert token_service.cached_token_data is not None, "background thread never recovered the token"
        assert token_service.cached_token_data.access_token == "recovered_token"
        assert len(responses.calls) == 2

    @responses.activate
    def test_construction_retries_on_too_many_requests_via_background(self):
        cur = int(time())
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=429)
        _add_oauth_mock(json_body=_token_json(cur, cur + 5014))

        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id", client_version=1,
                                                                        client_secret="client_secret"),
                                     env=Env.SANDBOX, event_publisher=EventPublisher())
        self.addCleanup(token_service.close)

        assert token_service.cached_token_data is None  # rate-limited on the synchronous attempt
        assert len(responses.calls) == 1

        deadline = time() + 2
        while token_service.cached_token_data is None and time() < deadline:
            pass
        assert token_service.cached_token_data is not None
        assert len(responses.calls) == 2

    @responses.activate
    def test_force_refresh_token(self):
        _add_oauth_mock()
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id", client_version=1,
                                                                        client_secret="client_secret"),
                                     env=Env.SANDBOX, event_publisher=EventPublisher())
        self.addCleanup(token_service.close)
        assert len(responses.calls) == 1

        _add_oauth_mock(json_body=_token_json(int(time()), int(time()) + 5014, access_token="refreshed_token"))
        token_service.force_refresh_token()
        assert len(responses.calls) == 2
        assert token_service.cached_token_data.access_token == "refreshed_token"

    @responses.activate
    def test_close_stops_background_thread(self):
        _add_oauth_mock()
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id", client_version=1,
                                                                        client_secret="client_secret"),
                                     env=Env.SANDBOX, event_publisher=EventPublisher())
        self.addCleanup(token_service.close)
        assert token_service._background_thread.is_alive()
        token_service.close()
        assert not token_service._background_thread.is_alive()
        # calling close() again (including via addCleanup afterward) must be safe (no exception)

    @responses.activate
    def test_proactive_background_refresh_fires_at_half_life(self):
        cur = int(time_module.time())
        _add_oauth_mock(json_body=_token_json(cur, cur + 2, access_token="token_1"))
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id", client_version=1,
                                                                        client_secret="client_secret"),
                                     env=Env.SANDBOX, event_publisher=EventPublisher())
        self.addCleanup(token_service.close)
        assert len(responses.calls) == 1
        assert token_service.cached_token_data.access_token == "token_1"

        _add_oauth_mock(json_body=_token_json(int(time_module.time()) + 1, int(time_module.time()) + 201,
                                              access_token="token_2"))

        time_module.sleep(1.5)  # past the ~1s half-life of the first token

        assert len(responses.calls) == 2, "expected the background thread to have proactively refreshed"
        assert token_service.cached_token_data.access_token == "token_2"

    @responses.activate
    def test_proactive_background_refresh_does_not_busy_loop_on_persistent_failure(self):
        # Worst case: the server keeps returning a token that's already past its own half-life
        # (or the fetch keeps failing) - the background loop must stay safely paced, never a
        # tight zero-delay loop.
        cur = int(time_module.time())
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=_token_json(cur, cur + 2))
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id", client_version=1,
                                                                        client_secret="client_secret"),
                                     env=Env.SANDBOX, event_publisher=EventPublisher())
        self.addCleanup(token_service.close)
        assert len(responses.calls) == 1

        time_module.sleep(2.5)

        # Paced by MIN_SECONDS_BETWEEN_PROACTIVE_ATTEMPTS (1s floor) - definitely not hundreds of
        # calls in 2.5 real seconds.
        assert len(responses.calls) < 10, f"background loop appears to be busy-looping: {len(responses.calls)} calls"

    def test_static(self):
        with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
            mock.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                    json=_token_json(int(time()), int(time()) + 5014))
            instance = StandardCheckoutClient.get_instance(
                client_id="client_id_02",
                client_secret="client_secret",
                client_version=1,
                env=Env.SANDBOX
            )

            instance1 = StandardCheckoutClient.get_instance(
                client_id="client_id_03",
                client_secret="client_secret3",
                client_version=1,
                env=Env.SANDBOX
            )

            instance2 = StandardCheckoutClient.get_instance(
                client_id="client_id_02",
                client_secret="client_secret",
                client_version=1,
                env=Env.SANDBOX
            )

        # instance/instance1/instance2 are cached singletons shared with other tests (e.g.
        # test_singleton.py reuses the same client_id/client_secret) - deliberately NOT closed
        # here, since doing so would tear down connections/background threads still needed by
        # whichever test runs next and reuses the same cached instance.
        token_service = instance._token_service
        token_service1 = instance1._token_service
        token_service2 = instance2._token_service

        token_service.cached_token_data = "demo"

        assert token_service2 is token_service
        self.assertTrue(token_service.get_auth_token == token_service2.get_auth_token)

        self.assertTrue(token_service.get_auth_token != token_service1.get_auth_token)

        token_service.cached_token_data = "1"
        assert token_service.cached_token_data != token_service1.cached_token_data

        token_service.cached_token_data = token_service1.cached_token_data
        assert token_service.cached_token_data == token_service1.cached_token_data
