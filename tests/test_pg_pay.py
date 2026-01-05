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

from phonepe.sdk.pg.common.models.request.payment_mode_constraints.card_payment_mode import (
    CardPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.card_type import CardType
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.net_banking_payment_mode import (
    NetBankingPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.upi_collect_payment_mode import (
    UpiCollectPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.upi_intent_payment_mode import (
    UpiIntentPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.upi_qr_payment_mode import (
    UpiQrPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.pg_payment_request import PgPaymentRequest
from phonepe.sdk.pg.common.models.request.pg_v2_instrument_type import (
    PgV2InstrumentType,
)
from phonepe.sdk.pg.common.models.response.pg_payment_response import PgPaymentResponse
from phonepe.sdk.pg.env import Env, get_pg_base_url
from phonepe.sdk.pg.payments.v2.custom_checkout.custom_checkout_constants import (
    PAY_API as PAY_API_CUSTOM,
)
from phonepe.sdk.pg.payments.v2.models.request.payment_mode_config import (
    PaymentModeConfig,
)
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import (
    StandardCheckoutPayRequest,
)
from phonepe.sdk.pg.payments.v2.models.response.standard_checkout_pay_response import (
    StandardCheckoutPayResponse,
)
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import (
    PAY_API,
)
from tests.base_test_with_oauth import BaseTestWithOauth


class PayTestWithOauth(BaseTestWithOauth):

    @responses.activate
    def test_pay_page(self):
        response_string = """{"orderId": "OMO2403071446458436434329", "state": "PENDING", "expireAt": 1709803425841, "redirectUrl": "mercury.com"}"""

        client_secret = "client_secret"
        client_id = "client_id"
        client_version = 1

        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        enabled_modes_data = [
            UpiIntentPaymentModeConstraint(PgV2InstrumentType.UPI_INTENT),
            UpiCollectPaymentModeConstraint(PgV2InstrumentType.UPI_COLLECT),
            UpiQrPaymentModeConstraint(PgV2InstrumentType.UPI_QR),
            NetBankingPaymentModeConstraint(PgV2InstrumentType.NET_BANKING),
            CardPaymentModeConstraint(card_types=[CardType.DEBIT_CARD, CardType.CREDIT_CARD]),
        ]
        payment_mode_config = PaymentModeConfig(
            enabled_payment_modes=enabled_modes_data
        )
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="MOID01",
            amount=1000,
            redirect_url="url.com",
            payment_mode_config=payment_mode_config,
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + PAY_API,
            status=200,
            json=json.loads(response_string),
        )

        actual_response = standard_checkout_client.pay(pay_request=pay_request)
        expected_response = StandardCheckoutPayResponse(
            order_id="OMO2403071446458436434329",
            state="PENDING",
            expire_at=1709803425841,
            redirect_url="mercury.com",
        )
        assert expected_response == actual_response

    @responses.activate
    def test_pay_page_custom(self):
        response_string = """{"orderId": "OMO2403071446458436434329", "state": "PENDING", "expireAt": 1709803425841, "redirectUrl": "mercury.com"}"""

        client_secret = "client_secret"
        client_id = "client_id"
        client_version = 1

        custom_client = BaseTestWithOauth.custom_checkout_client
        pay_request = PgPaymentRequest.build_upi_intent_pay_request(
            merchant_order_id="order", amount=100
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + PAY_API_CUSTOM,
            status=200,
            json=json.loads(response_string),
        )

        actual_response = custom_client.pay(pay_request=pay_request)
        expected_response = PgPaymentResponse(
            order_id="OMO2403071446458436434329",
            state="PENDING",
            expire_at=1709803425841,
            redirect_url="mercury.com",
        )
        assert expected_response == actual_response

    @responses.activate
    def test_pay_page_disable_payment_retry(self):
        response_string = """{"orderId": "OMO2403071446458436434329", "state": "PENDING", "expireAt": 1709803425841, "redirectUrl": "mercury.com"}"""

        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="MOID01",
            amount=1000,
            redirect_url="url.com",
            disable_payment_retry=True,
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + PAY_API,
            status=200,
            json=json.loads(response_string),
        )

        actual_response = standard_checkout_client.pay(pay_request=pay_request)
        expected_response = StandardCheckoutPayResponse(
            order_id="OMO2403071446458436434329",
            state="PENDING",
            expire_at=1709803425841,
            redirect_url="mercury.com",
        )
        assert pay_request.disable_payment_retry
        assert expected_response == actual_response

    @responses.activate
    def test_pay_page_enabled_payment_retry(self):
        response_string = """{"orderId": "OMO2403071446458436434329", "state": "PENDING", "expireAt": 1709803425841, "redirectUrl": "mercury.com"}"""

        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="MOID01",
            amount=1000,
            redirect_url="url.com",
            disable_payment_retry=False,
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + PAY_API,
            status=200,
            json=json.loads(response_string),
        )

        actual_response = standard_checkout_client.pay(pay_request=pay_request)
        expected_response = StandardCheckoutPayResponse(
            order_id="OMO2403071446458436434329",
            state="PENDING",
            expire_at=1709803425841,
            redirect_url="mercury.com",
        )
        assert not pay_request.disable_payment_retry
        assert expected_response == actual_response
