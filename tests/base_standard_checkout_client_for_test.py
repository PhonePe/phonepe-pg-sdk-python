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

from unittest import TestCase

import responses

from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.env import Env, get_oauth_base_url
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient

_TOKEN_RESPONSE = {
    "access_token": "access_token",
    "encrypted_access_token": "encrypted_access_token",
    "refresh_token": "refresh_token",
    "expires_in": 5014,
    "issued_at": 2014804440,
    "expires_at": 2014804440,
    "session_expires_at": 2014804440,
    "token_type": "O-Bearer",
}


class BaseStandardCheckoutClientForTest(TestCase):
    standard_checkout_client = None

    @responses.activate
    def setUp(self) -> None:
        # Client construction now eagerly fetches an OAuth token (see TokenService), so setUp()
        # needs its own active responses mock covering that fetch - the test method's own
        # @responses.activate (if any) only wraps the method itself, not setUp(), which
        # unittest/pytest always calls beforehand, outside that decorator's scope. Once the
        # singleton for this client_id/config already exists (from an earlier test), get_instance
        # just returns the cached instance with no new HTTP call, so this mock is harmless then.
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=_TOKEN_RESPONSE)
        BaseStandardCheckoutClientForTest.standard_checkout_client = StandardCheckoutClient.get_instance(
            client_id="client_id",
            client_version=1,
            client_secret="client_secret",
            env=Env.SANDBOX,
            should_publish_events=False)
        self.addCleanup(BaseStandardCheckoutClientForTest.standard_checkout_client.close)

    @staticmethod
    def get_standard_checkout_client():
        # Always resolve through get_instance(): the cached attribute can point at a client a
        # previous test closed (and therefore evicted from the singleton cache).
        with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
            mock.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                     json=_TOKEN_RESPONSE)
            BaseStandardCheckoutClientForTest.standard_checkout_client = StandardCheckoutClient.get_instance(
                client_id="client_id",
                client_version=1,
                client_secret="client_secret",
                env=Env.SANDBOX,
                should_publish_events=False)
        return BaseStandardCheckoutClientForTest.standard_checkout_client
