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
from phonepe.sdk.pg.payments.v2.models.request.pg_v2_instrument_type import (
    PgV2InstrumentType,
)
from phonepe.sdk.pg.payments.v2.models.response.payment_refund_detail import (
    PaymentRefundDetail,
)
from phonepe.sdk.pg.common.models.response.refund_status_response import (
    RefundStatusResponse,
)
from phonepe.sdk.pg.payments.v2.custom_checkout.custom_checkout_constants import (
    REFUND_STATUS_API,
)
from tests.base_test_with_oauth import BaseTestWithOauth


class TestRefundStatusWithOauth(BaseTestWithOauth):

    @responses.activate
    def test_refund_status_success(self):
        response_string = """{
            "merchantId": "MID",
            "merchantRefundId": "merchant_refund_id",
            "originalMerchantOrderId": "Merchant1709808573",
            "amount": 100,
            "state": "CONFIRMED",
            "paymentDetails": [
                {
                    "transactionId": "OMR2403071623443032708524",
                    "paymentMode": "UPI_INTENT",
                    "timestamp": 1709808824322,
                    "amount": 100,
                    "state": "CONFIRMED",
                    "responseCode": "PAYMENT_SUCCESS",
                    "backendErrorCode": "SUCCESS"
                }
            ]
        }"""
        merchant_refund_id = "merchant_refund_id"
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        responses.add(
            responses.GET,
            get_pg_base_url(Env.SANDBOX)
            + REFUND_STATUS_API.format(merchant_refund_id=merchant_refund_id),
            status=200,
            json=json.loads(response_string),
        )
        expected_refund_response = RefundStatusResponse(
            merchant_id="MID",
            merchant_refund_id="merchant_refund_id",
            original_merchant_order_id="Merchant1709808573",
            amount=100,
            state="CONFIRMED",
            payment_details=[
                PaymentRefundDetail(
                    transaction_id="OMR2403071623443032708524",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1709808824322,
                    amount=100,
                    state="CONFIRMED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=None,
                    rail=None,
                )
            ],
        )

        actual_refund_response = standard_checkout_client.get_refund_status(
            merchant_refund_id=merchant_refund_id
        )
        assert expected_refund_response == actual_refund_response

    @responses.activate
    def test_refund_status_success_custom(self):
        response_string = """{
            "merchantId": "MID",
            "merchantRefundId": "merchant_refund_id",
            "originalMerchantOrderId": "Merchant1709808573",
            "amount": 100,
            "state": "CONFIRMED",
            "paymentDetails": [
                {
                    "transactionId": "OMR2403071623443032708524",
                    "paymentMode": "UPI_INTENT",
                    "timestamp": 1709808824322,
                    "amount": 100,
                    "state": "CONFIRMED",
                    "responseCode": "PAYMENT_SUCCESS",
                    "backendErrorCode": "SUCCESS"
                }
            ]
        }"""
        merchant_refund_id = "merchant_refund_id"
        custom_checkout_client = BaseTestWithOauth.custom_checkout_client
        responses.add(
            responses.GET,
            get_pg_base_url(Env.SANDBOX)
            + REFUND_STATUS_API.format(merchant_refund_id=merchant_refund_id),
            status=200,
            json=json.loads(response_string),
        )
        expected_refund_response = RefundStatusResponse(
            merchant_id="MID",
            merchant_refund_id="merchant_refund_id",
            original_merchant_order_id="Merchant1709808573",
            amount=100,
            state="CONFIRMED",
            payment_details=[
                PaymentRefundDetail(
                    transaction_id="OMR2403071623443032708524",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1709808824322,
                    amount=100,
                    state="CONFIRMED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=None,
                    rail=None,
                )
            ],
        )

        actual_refund_response = custom_checkout_client.get_refund_status(
            merchant_refund_id=merchant_refund_id
        )
        assert expected_refund_response == actual_refund_response

    @responses.activate
    def test_refund_status_success_subscription(self):
        response_string = """{
            "merchantId": "MID",
            "merchantRefundId": "merchant_refund_id",
            "originalMerchantOrderId": "Merchant1709808573",
            "amount": 100,
            "state": "CONFIRMED",
            "paymentDetails": [
                {
                    "transactionId": "OMR2403071623443032708524",
                    "paymentMode": "UPI_INTENT",
                    "timestamp": 1709808824322,
                    "amount": 100,
                    "state": "CONFIRMED",
                    "responseCode": "PAYMENT_SUCCESS",
                    "backendErrorCode": "SUCCESS"
                }
            ]
        }"""
        merchant_refund_id = "merchant_refund_id"
        subscription_client = BaseTestWithOauth.subscription_client
        responses.add(
            responses.GET,
            get_pg_base_url(Env.SANDBOX)
            + REFUND_STATUS_API.format(merchant_refund_id=merchant_refund_id),
            status=200,
            json=json.loads(response_string),
        )
        expected_refund_response = RefundStatusResponse(
            merchant_id="MID",
            merchant_refund_id="merchant_refund_id",
            original_merchant_order_id="Merchant1709808573",
            amount=100,
            state="CONFIRMED",
            payment_details=[
                PaymentRefundDetail(
                    transaction_id="OMR2403071623443032708524",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1709808824322,
                    amount=100,
                    state="CONFIRMED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=None,
                    rail=None,
                )
            ],
        )
        actual_refund_response = subscription_client.get_refund_status(
            merchant_refund_id=merchant_refund_id
        )
        assert expected_refund_response == actual_refund_response
