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

import responses

from phonepe.sdk.pg.env import Env, get_pg_base_url
from phonepe.sdk.pg.payments.v2.custom_checkout.custom_checkout_constants import (
    REFUND_API as REFUND_API_CUSTOM,
)
from phonepe.sdk.pg.common.models.request.refund_request import RefundRequest
from phonepe.sdk.pg.common.models.response.refund_response import RefundResponse
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import (
    REFUND_API,
)
from phonepe.sdk.pg.subscription.v2.models.subscription_constants import REFUND_API
from tests.base_test_with_oauth import BaseTestWithOauth


class TestRefundWithOauth(BaseTestWithOauth):
    @responses.activate
    def test_refund_success(self):
        response_string = (
            """{"refundId": "OMR5757225", "amount": 3, "state": "PENDING"}"""
        )

        refund_request = RefundRequest.build_refund_request(
            merchant_refund_id="merchant_refund_id",
            amount=100,
            original_merchant_order_id="original_merchant_order_id",
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + REFUND_API,
            status=200,
            json=json.loads(response_string),
        )
        pay_response = BaseTestWithOauth.standard_checkout_client.refund(
            refund_request=refund_request
        )
        expected_response = RefundResponse(
            refund_id="OMR5757225", amount=3, state="PENDING"
        )

        assert pay_response == expected_response

    @responses.activate
    def test_refund_success_custom(self):
        response_string = (
            """{"refundId": "OMR5757225", "amount": 3, "state": "PENDING"}"""
        )

        refund_request = RefundRequest.build_refund_request(
            merchant_refund_id="merchant_refund_id",
            amount=100,
            original_merchant_order_id="original_merchant_order_id",
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + REFUND_API_CUSTOM,
            status=200,
            json=json.loads(response_string),
        )
        pay_response = BaseTestWithOauth.custom_checkout_client.refund(
            refund_request=refund_request
        )
        expected_response = RefundResponse(
            refund_id="OMR5757225", amount=3, state="PENDING"
        )

        assert pay_response == expected_response

    @responses.activate
    def test_refund_success_subscription(self):
        response_string = (
            """{"refundId": "OMR5757225", "amount": 3, "state": "PENDING"}"""
        )

        refund_request = RefundRequest.build_refund_request(
            merchant_refund_id="merchant_refund_id",
            amount=100,
            original_merchant_order_id="original_merchant_order_id",
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + REFUND_API,
            status=200,
            json=json.loads(response_string),
        )
        pay_response = BaseTestWithOauth.subscription_client.refund(
            refund_request=refund_request
        )
        expected_response = RefundResponse(
            refund_id="OMR5757225", amount=3, state="PENDING"
        )

        assert pay_response == expected_response
