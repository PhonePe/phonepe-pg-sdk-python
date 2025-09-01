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
from unittest import TestCase

import responses

from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.common.token_handler.token_service import TokenService
from phonepe.sdk.pg.env import Env, get_oauth_base_url
from phonepe.sdk.pg.payments.v2.custom_checkout_client import CustomCheckoutClient
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.subscription.v2.subscription_client import SubscriptionClient


class BaseTestWithOauth(TestCase):
    standard_checkout_client = None
    custom_checkout_client = None
    subscription_client = None

    def setUp(self) -> None:
        token_response_data = """{
                                    "access_token": "access_token",
                                    "encrypted_access_token": "encrypted_access_token",
                                    "refresh_token": "refresh_token",
                                    "expires_in": 5014,
                                    "issued_at": 2014804440,
                                    "expires_at": 2014804440,
                                    "session_expires_at": 2014804440,
                                    "token_type": "O-Bearer"
                                }
                                """

        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))
        BaseTestWithOauth.standard_checkout_client = StandardCheckoutClient.get_instance(client_id="client_id",
                                                                                         client_version=1,
                                                                                         client_secret="client_secret",
                                                                                         env=Env.SANDBOX,
                                                                                         should_publish_events=False)

        BaseTestWithOauth.custom_checkout_client = CustomCheckoutClient.get_instance(client_id="client_id",
                                                                                     client_version=1,
                                                                                     client_secret="client_secret",
                                                                                     env=Env.SANDBOX,
                                                                                     should_publish_events=False)

        BaseTestWithOauth.subscription_client = SubscriptionClient.get_instance(client_id="client_id",
                                                                                client_version=1,
                                                                                client_secret="client_secret",
                                                                                env=Env.SANDBOX,
                                                                                should_publish_events=False)
