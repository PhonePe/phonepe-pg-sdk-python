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
from time import time
from unittest import TestCase
from unittest.mock import call, patch, MagicMock

import responses

from phonepe.sdk.pg.common.configs.credential_config import CredentialConfig
from phonepe.sdk.pg.common.events.models.enums.event_type import EventType
from phonepe.sdk.pg.common.events.publisher.event_publisher import EventPublisher
from phonepe.sdk.pg.common.exceptions import BadRequest, PhonePeException, ServerError, TooManyRequests, UnauthorizedAccess
from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.common.token_handler.token_service import TokenService
from phonepe.sdk.pg.env import Env, get_oauth_base_url
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient


class TestTokenService(TestCase):

    @responses.activate
    def test_fetch_token(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        token_response_data = """{
                                            "access_token": "access_token",
                                            "encrypted_access_token": "encrypted_access_token",
                                            "refresh_token": "d0e89cb1-2b3b-41b8-87d9-31411c60edb7",
                                            "expires_in": 5014,
                                            "issued_at": 1709623116,
                                            "expires_at": 1709630316,
                                            "session_expires_at": 1709630316,
                                            "token_type": "O-Bearer"
                                        }
                                        """
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        assert "O-Bearer access_token" == token_service.get_auth_token()

    @responses.activate
    def test_token_refresh(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        token_response_data = """{
                                        "access_token": "access_token",
                                        "encrypted_access_token": "encrypted_access_token",
                                        "refresh_token": "d0e89cb1-2b3b-41b8-87d9-31411c60edb7",
                                        "expires_in": 0,
                                        "issued_at": 0,
                                        "expires_at": 1709630316,
                                        "session_expires_at": 1709630316,
                                        "token_type": "O-Bearer"
                                        }
                                    """
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        set_token = token_service.get_auth_token()  # sets expired token
        refresh_attempt = token_service.get_auth_token()  # notices token is expired and fetches new token

        assert len(responses.calls) == 2

    @responses.activate
    def test_token_use_cached(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        token_response_data = """{
                                            "access_token": "access_token",
                                            "encrypted_access_token": "encrypted_access_token",
                                            "refresh_token": "refresh_token",
                                            "expires_in": 2147483647,
                                            "issued_at": 1709630316,
                                            "expires_at": 2147483647,
                                            "session_expires_at": 1709630316,
                                            "token_type": "O-Bearer"
                                            }
                                        """
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        set_token = token_service.get_auth_token()  # sets expired token
        no_refresh = token_service.get_auth_token()  # notices token is valid and does not fetch new token
        assert len(responses.calls) == 1

    @responses.activate
    def test_token_use_cached(self):

        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        cur_time = int(time())  # Example value for cur_time
        two_sec_more_cur = int(cur_time + 2)

        token_response_data = f"""{{
            "access_token": "access_token",
            "encrypted_access_token": "encrypted_access_token",
            "refresh_token": "refresh_token",
            "expires_in": 200,
            "issued_at": {cur_time},
            "expires_at": {two_sec_more_cur},
            "session_expires_at": 1709630316,
            "token_type": "O-Bearer"
        }}
        """
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        set_token = token_service.get_auth_token()  # sets valid token
        set_token = token_service.get_auth_token()
        set_token = token_service.get_auth_token()

        assert len(responses.calls) == 1

        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 1)):
            set_token = token_service.get_auth_token()  # tries to fetch new token
            set_token = token_service.get_auth_token()  # tries to fetch new token
            set_token = token_service.get_auth_token()  # tries to fetch new token

        assert len(responses.calls) == 4

    @responses.activate
    def test_token_use_cached_then_cached_valid2(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        cur_time = int(time())  # Example value for cur_time
        four_sec_more = cur_time + 4
        ten_sec_more = cur_time + 10

        token_response_data = f"""{{
                "access_token": "access_token",
                "encrypted_access_token": "encrypted_access_token",
                "refresh_token": "refresh_token",
                "expires_in": 200,
                "issued_at": {cur_time},
                "expires_at": {four_sec_more},
                "session_expires_at": 1709630316,
                "token_type": "O-Bearer"
            }}
            """
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        set_token = token_service.get_auth_token()  # sets valid token
        set_token = token_service.get_auth_token()
        set_token = token_service.get_auth_token()

        assert len(responses.calls) == 1

        token_response_data = f"""{{
                        "access_token": "access_token",
                        "encrypted_access_token": "encrypted_access_token",
                        "refresh_token": "refresh_token",
                        "expires_in": 200,
                        "issued_at": {cur_time},
                        "expires_at": {ten_sec_more},
                        "session_expires_at": 1709630316,
                        "token_type": "O-Bearer"
                    }}
                    """
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 1)):
            set_token = token_service.get_auth_token()  # does not fetch, uses old token
        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 2)):
            set_token = token_service.get_auth_token()  # fetches new token
        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 3)):
            set_token = token_service.get_auth_token()  # uses old token
        with patch.object(token_service, 'get_current_time', return_value=(cur_time + 4)):
            set_token = token_service.get_auth_token()  # uses old token
        assert len(responses.calls) == 2

    @responses.activate
    def test_first_fetch_token_failure(self):

        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        token_response_data = """{
                                "code": "INVALID_CLIENT",
                                "errorCode": "OIM000",
                                "message": "Bad Request: Invalid Client, trackingId: 2123d",
                                "context": {
                                    "error_description": "Client authentication failure"
                                }
                            }"""
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=400,
                      json=json.loads(token_response_data))

        self.assertRaises(PhonePeException, token_service.get_auth_token)

    @responses.activate
    def test_first_fetch_works_second_fetch_fails_sends_back_old_token(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        cur_time = int(time())  # Example value for cur_time
        two_sec_less_cur = int(cur_time - 2)

        token_response_data = f"""{{
                "access_token": "access_token",
                "encrypted_access_token": "encrypted_access_token",
                "refresh_token": "refresh_token",
                "expires_in": 200,
                "issued_at": {two_sec_less_cur},
                "expires_at": {cur_time},
                "session_expires_at": 1709630316,
                "token_type": "O-Bearer"
            }}
            """  # this token is expired
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        set_token = token_service.get_auth_token()  # sets valid token
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=342)

        should_receive_old_token1 = token_service.get_auth_token()
        should_receive_old_token2 = token_service.get_auth_token()
        should_receive_old_token3 = token_service.get_auth_token()

        assert "O-Bearer access_token" == set_token
        assert "O-Bearer access_token" == should_receive_old_token1
        assert "O-Bearer access_token" == should_receive_old_token2
        assert "O-Bearer access_token" == should_receive_old_token3
        assert len(responses.calls) == 4  # (1 set token, 3 attempts to fetch new token but failed)

    def test_max_retries_constant(self):
        # Guards against accidental changes to the configured retry budget
        assert TokenService.MAX_RETRIES == 3

    @responses.activate
    @patch("phonepe.sdk.pg.common.token_handler.token_service.sleep")
    def test_retry_succeeds_after_transient_failures_when_no_cached_token(self, mock_sleep):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        token_response_data = """{
                                    "access_token": "access_token",
                                    "encrypted_access_token": "encrypted_access_token",
                                    "refresh_token": "d0e89cb1-2b3b-41b8-87d9-31411c60edb7",
                                    "expires_in": 5014,
                                    "issued_at": 1709623116,
                                    "expires_at": 1709630316,
                                    "session_expires_at": 1709630316,
                                    "token_type": "O-Bearer"
                                }"""
        # First two attempts fail with a transient server error, third succeeds
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=500)
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=500)
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        token = token_service.get_auth_token()

        assert token == "O-Bearer access_token"
        assert len(responses.calls) == 3  # 2 failed retries + 1 successful attempt
        assert token_service.cached_token_data is not None
        # backoff sleeps between the 2 failed attempts (1s, then 2s), none after the final success
        assert mock_sleep.call_args_list == [call(1), call(2)]

    @responses.activate
    @patch("phonepe.sdk.pg.common.token_handler.token_service.sleep")
    def test_retry_exhausted_raises_when_no_cached_token(self, mock_sleep):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        for _ in range(TokenService.MAX_RETRIES):
            responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=500)

        self.assertRaises(ServerError, token_service.get_auth_token)

        assert len(responses.calls) == TokenService.MAX_RETRIES  # exactly MAX_RETRIES attempts, no more
        assert token_service.cached_token_data is None
        # no sleep after the final (3rd) failed attempt since we're about to give up
        assert mock_sleep.call_args_list == [call(1), call(2)]

    @responses.activate
    @patch("phonepe.sdk.pg.common.token_handler.token_service.sleep")
    def test_retry_exhausted_publishes_none_cached_token_event(self, mock_sleep):
        mock_event_publisher = MagicMock(spec=EventPublisher)
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=mock_event_publisher)
        # reset the mock so the TOKEN_SERVICE_INITIALIZED init event doesn't interfere with assertions below
        mock_event_publisher.send.reset_mock()

        for _ in range(TokenService.MAX_RETRIES):
            responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=500)

        self.assertRaises(ServerError, token_service.get_auth_token)

        published_event_names = [call.args[0].event_name for call in mock_event_publisher.send.call_args_list]
        assert EventType.OAUTH_FETCH_FAILED_NONE_CACHED_TOKEN in published_event_names

    @responses.activate
    def test_no_retry_when_cached_token_exists_and_refresh_fails(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        cur_time = int(time())
        two_sec_less_cur = int(cur_time - 2)

        token_response_data = f"""{{
                "access_token": "access_token",
                "encrypted_access_token": "encrypted_access_token",
                "refresh_token": "refresh_token",
                "expires_in": 200,
                "issued_at": {two_sec_less_cur},
                "expires_at": {cur_time},
                "session_expires_at": 1709630316,
                "token_type": "O-Bearer"
            }}
            """  # already expired, so next get_auth_token triggers a refresh
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        token_service.get_auth_token()  # sets the cached (already expired) token
        assert len(responses.calls) == 1

        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=500)

        token = token_service.get_auth_token()  # refresh fails, falls back to cached token, no retries

        assert token == "O-Bearer access_token"
        # If the SDK retried on this path (like it does when there's no cached token),
        # this would be 1 (initial) + MAX_RETRIES (3) = 4 calls instead of 2.
        assert len(responses.calls) == 2  # 1 initial fetch + exactly 1 failed refresh attempt (no retries)

    @responses.activate
    def test_no_retry_on_bad_request_when_no_cached_token(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        # e.g. "form field grant_type must not be blank." - retrying won't fix a malformed request
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=400,
                      json={"success": False, "code": "BAD_REQUEST", "message": "form field grant_type must not be blank.", "data": {}})

        self.assertRaises(BadRequest, token_service.get_auth_token)

        assert len(responses.calls) == 1  # fails fast, no retries for a genuine bad request
        assert token_service.cached_token_data is None

    @responses.activate
    def test_no_retry_on_unauthorized_when_no_cached_token(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        # e.g. invalid client_id/client_secret - retrying with the same credentials will always fail
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=401,
                      json={"success": False, "code": "401"})

        self.assertRaises(UnauthorizedAccess, token_service.get_auth_token)

        assert len(responses.calls) == 1  # fails fast, no retries for invalid credentials
        assert token_service.cached_token_data is None

    @responses.activate
    @patch("phonepe.sdk.pg.common.token_handler.token_service.sleep")
    def test_retries_on_too_many_requests_when_no_cached_token(self, mock_sleep):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        token_response_data = """{
                                    "access_token": "access_token",
                                    "encrypted_access_token": "encrypted_access_token",
                                    "refresh_token": "d0e89cb1-2b3b-41b8-87d9-31411c60edb7",
                                    "expires_in": 5014,
                                    "issued_at": 1709623116,
                                    "expires_at": 1709630316,
                                    "session_expires_at": 1709630316,
                                    "token_type": "O-Bearer"
                                }"""
        # 429 (rate limited) is transient, unlike other 4xx errors, so it should still be retried
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=429)
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        token = token_service.get_auth_token()

        assert token == "O-Bearer access_token"
        assert len(responses.calls) == 2  # 1 rate-limited attempt + 1 successful retry
        assert mock_sleep.call_args_list == [call(1)]  # 1s backoff before the retry

    @responses.activate
    @patch("phonepe.sdk.pg.common.token_handler.token_service.sleep")
    def test_too_many_requests_exhausted_raises_when_no_cached_token(self, mock_sleep):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        for _ in range(TokenService.MAX_RETRIES):
            responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=429)

        self.assertRaises(TooManyRequests, token_service.get_auth_token)

        assert len(responses.calls) == TokenService.MAX_RETRIES
        assert mock_sleep.call_args_list == [call(1), call(2)]

    def test_retry_backoff_delay_is_exponential(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        assert token_service._get_retry_delay(1) == 1
        assert token_service._get_retry_delay(2) == 2
        assert token_service._get_retry_delay(3) == 4

    def test_should_retry_token_fetch_defaults_to_true(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher())
        assert token_service.should_retry_token_fetch is True

    @responses.activate
    @patch("phonepe.sdk.pg.common.token_handler.token_service.sleep")
    def test_no_retry_when_should_retry_token_fetch_is_false(self, mock_sleep):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher(),
                                     should_retry_token_fetch=False)
        for _ in range(TokenService.MAX_RETRIES):
            responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=500)

        self.assertRaises(ServerError, token_service.get_auth_token)

        assert len(responses.calls) == 1  # opted out of retries, so only 1 attempt is made
        mock_sleep.assert_not_called()
        assert token_service.cached_token_data is None

    @responses.activate
    def test_first_fetch_succeeds_when_should_retry_token_fetch_is_false(self):
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=EventPublisher(),
                                     should_retry_token_fetch=False)
        token_response_data = """{
                                    "access_token": "access_token",
                                    "encrypted_access_token": "encrypted_access_token",
                                    "refresh_token": "d0e89cb1-2b3b-41b8-87d9-31411c60edb7",
                                    "expires_in": 5014,
                                    "issued_at": 1709623116,
                                    "expires_at": 1709630316,
                                    "session_expires_at": 1709630316,
                                    "token_type": "O-Bearer"
                                }"""
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

        token = token_service.get_auth_token()

        assert token == "O-Bearer access_token"
        assert len(responses.calls) == 1

    def test_static(self):
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
