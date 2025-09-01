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
from unittest.mock import patch

import responses

from phonepe.sdk.pg.common.configs.credential_config import CredentialConfig
from phonepe.sdk.pg.common.events.publisher.event_publisher import EventPublisher
from phonepe.sdk.pg.common.exceptions import PhonePeException
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
