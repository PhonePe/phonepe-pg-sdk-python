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
    TRANSACTION_STATUS_API as TRANSACTION_STATUS_API_CUSTOM,
)
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.payments.v2.models.request.pg_v2_instrument_type import (
    PgV2InstrumentType,
)
from phonepe.sdk.pg.common.models.response.order_status_response import (
    OrderStatusResponse,
)
from phonepe.sdk.pg.payments.v2.models.response.payment_detail import PaymentDetail
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import (
    TRANSACTION_STATUS_API,
)
from phonepe.sdk.pg.subscription.v2.models.subscription_constants import (
    TRANSACTION_STATUS_API as SUBSCRIPTION_TRANSACTION_STATUS_API,
)
from tests.base_test_with_oauth import BaseTestWithOauth


class TestTransactionStatusWithOauth(BaseTestWithOauth):

    @responses.activate
    def test_transaction_status_success(self):
        response_string = """{
            "orderId": "order_id",
            "state": "PENDING",
            "amount": 1000,
            "expireAt": 1707380461388,
            "metaInfo": {
                "udf1": "dummy1",
                "udf2": "dummy2",
                "udf3": "dummy3",
                "udf4": "dummy4"
            },
            "paymentDetails": [
                {
                    "transactionId": "OM342",
                    "paymentMode": "UPI_INTENT",
                    "timestamp": 1707376884117,
                    "amount": 1000,
                    "state": "PENDING"
                }
            ]
        } """
        transaction_id = "transaction_id"
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        responses.add(
            responses.GET,
            get_pg_base_url(Env.SANDBOX)
            + TRANSACTION_STATUS_API.format(transaction_id=transaction_id),
            status=200,
            json=json.loads(response_string),
        )
        actual_tnx_response = standard_checkout_client.get_transaction_status(
            transaction_id=transaction_id
        )

        expected_response = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="order_id",
            state="PENDING",
            amount=1000,
            expire_at=1707380461388,
            detailed_error_code=None,
            error_code=None,
            meta_info=MetaInfo(
                udf1="dummy1", udf2="dummy2", udf3="dummy3", udf4="dummy4", udf5=None
            ),
            payment_details=[
                PaymentDetail(
                    transaction_id="OM342",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1707376884117,
                    amount=1000,
                    state="PENDING",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=None,
                    rail=None,
                    split_instruments=None,
                )
            ],
        )

        assert actual_tnx_response == expected_response

    @responses.activate
    def test_transaction_status_success_custom(self):
        response_string = """{
            "orderId": "order_id",
            "state": "PENDING",
            "amount": 1000,
            "expireAt": 1707380461388,
            "metaInfo": {
                "udf1": "dummy1",
                "udf2": "dummy2",
                "udf3": "dummy3",
                "udf4": "dummy4"
            },
            "paymentDetails": [
                {
                    "transactionId": "OM342",
                    "paymentMode": "UPI_INTENT",
                    "timestamp": 1707376884117,
                    "amount": 1000,
                    "state": "PENDING"
                }
            ]
        } """
        transaction_id = "transaction_id"
        custom_checkout_client = BaseTestWithOauth.custom_checkout_client
        responses.add(
            responses.GET,
            get_pg_base_url(Env.SANDBOX)
            + TRANSACTION_STATUS_API_CUSTOM.format(transaction_id=transaction_id),
            status=200,
            json=json.loads(response_string),
        )
        actual_tnx_response = custom_checkout_client.get_transaction_status(
            transaction_id=transaction_id
        )

        expected_response = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="order_id",
            state="PENDING",
            amount=1000,
            expire_at=1707380461388,
            detailed_error_code=None,
            error_code=None,
            meta_info=MetaInfo(
                udf1="dummy1", udf2="dummy2", udf3="dummy3", udf4="dummy4", udf5=None
            ),
            payment_details=[
                PaymentDetail(
                    transaction_id="OM342",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1707376884117,
                    amount=1000,
                    state="PENDING",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=None,
                    rail=None,
                    split_instruments=None,
                )
            ],
        )

        assert actual_tnx_response == expected_response

    @responses.activate
    def test_transaction_status_success_subscription(self):
        response_string = """{
            "orderId": "order_id",
            "state": "PENDING",
            "amount": 1000,
            "expireAt": 1707380461388,
            "metaInfo": {
                "udf1": "dummy1",
                "udf2": "dummy2",
                "udf3": "dummy3",
                "udf4": "dummy4"
            },
            "paymentDetails": [
                {
                    "transactionId": "OM342",
                    "paymentMode": "UPI_INTENT",
                    "timestamp": 1707376884117,
                    "amount": 1000,
                    "state": "PENDING"
                }
            ]
        } """
        transaction_id = "transaction_id"
        subscription_client = BaseTestWithOauth.subscription_client
        responses.add(
            responses.GET,
            get_pg_base_url(Env.SANDBOX)
            + SUBSCRIPTION_TRANSACTION_STATUS_API.format(transaction_id=transaction_id),
            status=200,
            json=json.loads(response_string),
        )
        actual_tnx_response = subscription_client.get_transaction_status(
            transaction_id=transaction_id
        )

        expected_response = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="order_id",
            state="PENDING",
            amount=1000,
            expire_at=1707380461388,
            detailed_error_code=None,
            error_code=None,
            meta_info=MetaInfo(
                udf1="dummy1", udf2="dummy2", udf3="dummy3", udf4="dummy4", udf5=None
            ),
            payment_details=[
                PaymentDetail(
                    transaction_id="OM342",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1707376884117,
                    amount=1000,
                    state="PENDING",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=None,
                    rail=None,
                    split_instruments=None,
                )
            ],
        )

        assert actual_tnx_response == expected_response
