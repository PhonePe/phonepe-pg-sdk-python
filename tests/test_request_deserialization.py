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

from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
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
from phonepe.sdk.pg.payments.v2.models.request.payment_mode_config import (
    PaymentModeConfig,
)
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import (
    StandardCheckoutPayRequest,
)


class TestRequestDeserialization(TestCase):
    enabled_modes_data = [
        UpiIntentPaymentModeConstraint(PgV2InstrumentType.UPI_INTENT),
        UpiCollectPaymentModeConstraint(PgV2InstrumentType.UPI_COLLECT),
        UpiQrPaymentModeConstraint(PgV2InstrumentType.UPI_QR),
        NetBankingPaymentModeConstraint(PgV2InstrumentType.NET_BANKING),
        CardPaymentModeConstraint(card_types=[CardType.DEBIT_CARD, CardType.CREDIT_CARD]),
    ]
    payment_mode_config = PaymentModeConfig(enabled_payment_modes=enabled_modes_data)

    def test_checkout_deserialization(self):
        obj1 = StandardCheckoutPayRequest.build_request(
            "moid", 10, "redirect-url", payment_mode_config=self.payment_mode_config
        )

        resp1 = """{"merchantOrderId": "moid", "amount": 10, "metaInfo": null, "paymentFlow": {"type": "PG_CHECKOUT", "message": null, "merchantUrls": {"redirectUrl": "redirect-url"}, "paymentModeConfig": {"enabledPaymentModes": [{"type": "UPI_INTENT"}, {"type": "UPI_COLLECT"}, {"type": "UPI_QR"}, {"type": "NET_BANKING"}, {"type": "CARD", "cardTypes": ["DEBIT_CARD", "CREDIT_CARD"]}], "disabledPaymentModes": null}}, "expireAfter": null, "disablePaymentRetry": null}"""
        assert obj1.to_json() == resp1

        obj2 = StandardCheckoutPayRequest.build_request(
            "moid",
            10,
            "redirect-url",
            meta_info=MetaInfo.build_meta_info(udf1="sad"),
            payment_mode_config=self.payment_mode_config,
        )
        resp2 = """{"merchantOrderId": "moid", "amount": 10, "metaInfo": {"udf1": "sad", "udf2": null, "udf3": null, "udf4": null, "udf5": null}, "paymentFlow": {"type": "PG_CHECKOUT", "message": null, "merchantUrls": {"redirectUrl": "redirect-url"}, "paymentModeConfig": {"enabledPaymentModes": [{"type": "UPI_INTENT"}, {"type": "UPI_COLLECT"}, {"type": "UPI_QR"}, {"type": "NET_BANKING"}, {"type": "CARD", "cardTypes": ["DEBIT_CARD", "CREDIT_CARD"]}], "disabledPaymentModes": null}}, "expireAfter": null, "disablePaymentRetry": null}"""
        assert obj2.to_json() == resp2

        obj3 = StandardCheckoutPayRequest.build_request(
            "moid",
            10,
            "redirect-url",
            meta_info=MetaInfo.build_meta_info(udf1="sad", udf5="udf5"),
            payment_mode_config=self.payment_mode_config,
        )

        resp3 = """{"merchantOrderId": "moid", "amount": 10, "metaInfo": {"udf1": "sad", "udf2": null, "udf3": null, "udf4": null, "udf5": "udf5"}, "paymentFlow": {"type": "PG_CHECKOUT", "message": null, "merchantUrls": {"redirectUrl": "redirect-url"}, "paymentModeConfig": {"enabledPaymentModes": [{"type": "UPI_INTENT"}, {"type": "UPI_COLLECT"}, {"type": "UPI_QR"}, {"type": "NET_BANKING"}, {"type": "CARD", "cardTypes": ["DEBIT_CARD", "CREDIT_CARD"]}], "disabledPaymentModes": null}}, "expireAfter": null, "disablePaymentRetry": null}"""
        assert obj3.to_json() == resp3

    def test_custom_deserialization(self):
        obj = PgPaymentRequest.build_net_banking_pay_request(
            merchant_order_id="asd", amount=100, bank_id="HDFC", redirect_url="ru"
        )
        reps1 = """{"merchantOrderId": "asd", "amount": 100, "metaInfo": null, "deviceContext": null, "paymentFlow": {"type": "PG", "paymentMode": {"type": "NET_BANKING", "bankId": "HDFC", "merchantUserId": null}, "merchantUrls": {"redirectUrl": "ru"}}, "constraints": null, "expireAfter": null, "expireAt": null}"""
        assert obj.to_json() == reps1

        obj = PgPaymentRequest.build_net_banking_pay_request(
            merchant_order_id="asd",
            amount=100,
            bank_id="HDFC",
            redirect_url="ru",
            expire_after=10,
        )
        reps1 = """{"merchantOrderId": "asd", "amount": 100, "metaInfo": null, "deviceContext": null, "paymentFlow": {"type": "PG", "paymentMode": {"type": "NET_BANKING", "bankId": "HDFC", "merchantUserId": null}, "merchantUrls": {"redirectUrl": "ru"}}, "constraints": null, "expireAfter": 10, "expireAt": null}"""
        assert obj.to_json() == reps1
