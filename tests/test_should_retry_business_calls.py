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
from unittest.mock import call, patch

import responses

from phonepe.sdk.pg.common.exceptions import ServerError
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand
from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.env import Env, get_oauth_base_url, get_pg_base_url
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import ORDER_STATUS_API
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient


class TestShouldRetryBusinessCalls(TestCase):
    """The public should_retry flag on client construction controls retries for both the initial
    OAuth token fetch AND every business API call made through the client (get_order_status, setup,
    notify, cancel, refund, etc.), since all of them funnel through BaseClient._request_with_token_invalidation
    -> BaseHttpCommand.request(should_retry=...)."""

    def _mock_token_fetch(self):
        token_response_data = """{
                                    "access_token": "access_token",
                                    "encrypted_access_token": "encrypted_access_token",
                                    "refresh_token": "refresh_token",
                                    "expires_in": 5014,
                                    "issued_at": 2014804440,
                                    "expires_at": 2014804440,
                                    "session_expires_at": 2014804440,
                                    "token_type": "O-Bearer"
                                }"""
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_should_retry_false_disables_retry_on_business_call(self, mock_sleep):
        self._mock_token_fetch()
        client = StandardCheckoutClient.get_instance(
            client_id="client_id_should_retry_business_false",
            client_secret="client_secret",
            client_version=1,
            env=Env.SANDBOX,
            should_publish_events=False,
            should_retry=False,
        )
        merchant_order_id = "merchant_order_id"
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_order_id
        )
        responses.add(responses.GET, check_status_url, status=500)
        responses.add(responses.GET, check_status_url, status=200, json={
            "orderId": "merchant-order-id", "state": "COMPLETED", "amount": 100, "expireAt": 172800000,
            "paymentDetails": [],
        })

        self.assertRaises(ServerError, client.get_order_status, merchant_order_id)

        # 1 token fetch + exactly 1 failed order-status attempt (no retries)
        assert len(responses.calls) == 2
        mock_sleep.assert_not_called()

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_should_retry_true_retries_on_business_call(self, mock_sleep):
        self._mock_token_fetch()
        client = StandardCheckoutClient.get_instance(
            client_id="client_id_should_retry_business_true",
            client_secret="client_secret",
            client_version=1,
            env=Env.SANDBOX,
            should_publish_events=False,
            should_retry=True,
        )
        merchant_order_id = "merchant_order_id"
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_order_id
        )
        responses.add(responses.GET, check_status_url, status=502)
        responses.add(responses.GET, check_status_url, status=200, json={
            "orderId": "merchant-order-id", "state": "COMPLETED", "amount": 100, "expireAt": 172800000,
            "paymentDetails": [],
        })

        response = client.get_order_status(merchant_order_id)

        assert response.state == "COMPLETED"
        # 1 token fetch + 1 failed order-status attempt + 1 successful retry
        assert len(responses.calls) == 3
        assert mock_sleep.call_args_list == [call(1)]

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_should_retry_false_retry_exhausted_default_still_matches_max_retries(self, mock_sleep):
        # Sanity check that default (True) exhausts the full retry budget before giving up.
        self._mock_token_fetch()
        client = StandardCheckoutClient.get_instance(
            client_id="client_id_should_retry_business_exhaust",
            client_secret="client_secret",
            client_version=1,
            env=Env.SANDBOX,
            should_publish_events=False,
        )
        merchant_order_id = "merchant_order_id"
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_order_id
        )
        for _ in range(BaseHttpCommand.MAX_RETRIES):
            responses.add(responses.GET, check_status_url, status=500)

        self.assertRaises(ServerError, client.get_order_status, merchant_order_id)

        # 1 token fetch + MAX_RETRIES failed order-status attempts
        assert len(responses.calls) == 1 + BaseHttpCommand.MAX_RETRIES
        assert mock_sleep.call_args_list == [call(1), call(2)]
