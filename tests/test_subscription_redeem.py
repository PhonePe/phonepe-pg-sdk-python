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

from dataclasses import asdict

import responses
from phonepe.sdk.pg.common.exceptions import BadRequest, PhonePeException
from phonepe.sdk.pg.common.http_client_modules.phonepe_response import PhonePeResponse
from phonepe.sdk.pg.env import Env, get_pg_base_url
from phonepe.sdk.pg.subscription.v2.models.response.subscription_redeem_response_v2 import (
    SubscriptionRedeemResponseV2,
)
from phonepe.sdk.pg.subscription.v2.models.subscription_constants import REDEEM_API
from http import HTTPStatus
from tests.base_test_with_oauth import BaseTestWithOauth


class SubscriptionRedeemTest(BaseTestWithOauth):

    @responses.activate
    def test_redeem_success(self):

        merchant_order_id = "merchantOrderId"
        response_str = """{
                        "transactionId" : "OMOxxx",
                        "state" : "PENDING"
                    }"""

        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + REDEEM_API,
            body=response_str,
            status=HTTPStatus.OK,
        )
        actual_response = BaseTestWithOauth.subscription_client.redeem(
            merchant_order_id
        )
        expected_response = SubscriptionRedeemResponseV2(
            transaction_id="OMOxxx", state="PENDING"
        )
        assert actual_response == expected_response

    @responses.activate
    def test_redeem_failure(self):

        merchant_order_id = "merchantOrderId"
        response_str = """{
                        "code" : "Bad Request",
                        "message" : "message",
                        "data" : {
                            "a" : "b"
                        }"""

        phonepe_response = PhonePeResponse(
            code="Bad Request", message="message", data={"a": "b"}
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + REDEEM_API,
            json=asdict(phonepe_response),
            status=HTTPStatus.BAD_REQUEST,
        )
        with self.assertRaises(PhonePeException) as cm:
            BaseTestWithOauth.subscription_client.redeem(merchant_order_id)

        self.assertEqual(cm.exception.http_status_code, 400)
        self.assertEqual(cm.exception.code, "Bad Request")
        self.assertIsInstance(cm.exception, BadRequest)
