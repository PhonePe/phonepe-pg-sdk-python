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
from http import HTTPStatus

import responses

from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.common.models.response.order_status_response import (
    OrderStatusResponse,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.account_payment_instrument_v2 import (
    AccountPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.credit_card_payment_instrument_v2 import (
    CreditCardPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.egv_payment_instrument_v2 import (
    EvgPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.net_banking_payment_instrument_v2 import (
    NetBankingPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.payment_instrument_v2_type import (
    PaymentInstrumentV2Type,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.wallet_payment_instrument_v2 import (
    WalletPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.rails.payment_rail_type import (
    PaymentRailType,
)
from phonepe.sdk.pg.common.models.response.rails.pg_payment_rail import PgPaymentRail
from phonepe.sdk.pg.common.models.response.rails.ppi_evg_payment_rail import (
    PpiEgvPaymentRail,
)
from phonepe.sdk.pg.common.models.response.rails.ppi_wallet_payment_rail import (
    PpiWalletPaymentRail,
)
from phonepe.sdk.pg.common.models.response.rails.upi_payment_rail import UpiPaymentRail
from phonepe.sdk.pg.env import Env, get_pg_base_url
from phonepe.sdk.pg.payments.v2.custom_checkout.custom_checkout_constants import (
    ORDER_STATUS_API as order_status_custom_api,
)
from phonepe.sdk.pg.payments.v2.models.request.pg_v2_instrument_type import (
    PgV2InstrumentType,
)
from phonepe.sdk.pg.payments.v2.models.response.instrument_combo import InstrumentCombo
from phonepe.sdk.pg.payments.v2.models.response.payment_detail import PaymentDetail
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import (
    ORDER_STATUS_API,
)
from phonepe.sdk.pg.subscription.v2.models.request.amount_type import AmountType
from phonepe.sdk.pg.subscription.v2.models.request.auth_workflow_type import (
    AuthWorkflowType,
)
from phonepe.sdk.pg.subscription.v2.models.request.frequency import Frequency
from phonepe.sdk.pg.subscription.v2.models.response.subscription_setup_payment_flow_response import (
    SubscriptionSetupPaymentFlowResponse,
)
from phonepe.sdk.pg.subscription.v2.models.subscription_constants import (
    ORDER_STATUS_API as SUBSCRIPTION_ORDER_STATUS_API,
)
from tests.base_test_with_oauth import BaseTestWithOauth


class OrderStatusTestWithOauth(BaseTestWithOauth):

    @responses.activate
    def test_check_status_success(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
                "orderId": "merchant-order-id",
                "state": "COMPLETED",
                "amount": 100,
                "expireAt": 172800000,
                "metaInfo": {
                    "udf1": "udf1",
                    "udf2": "udf2",
                    "udf3": "udf3"
                    },
                "paymentDetails": [
                  {
                    "paymentMode": "UPI_QR",
                    "transactionId": "tid",
                    "timestamp": 22,
                    "amount": 22,
                    "state": "COMPLETED",
                    "rail": {
                      "type": "UPI",
                      "utr": "<utr>",
                      "upiTransactionId": "<upiTransactionId>",
                      "vpa": "<vpa>"
                    },
                    "instrument": {
                      "type": "ACCOUNT",
                      "maskedAccountNumber": "<maskedAccountNumber>",
                      "accountType": "SAVINGS",
                      "accountHolderName": "<accountHolderName>",
                      "ifsc": "<ifsc>"
                    }
                  }
                ]
              }
        """
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        response_object = standard_checkout_client.get_order_status(
            merchant_order_id=merchant_transaction_id
        )
        expected_order_status_obj = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="merchant-order-id",
            state="COMPLETED",
            amount=100,
            expire_at=172800000,
            detailed_error_code=None,
            error_code=None,
            meta_info=MetaInfo(
                udf1="udf1", udf2="udf2", udf3="udf3", udf4=None, udf5=None
            ),
            payment_details=[
                PaymentDetail(
                    transaction_id="tid",
                    payment_mode=PgV2InstrumentType.UPI_QR,
                    timestamp=22,
                    amount=22,
                    state="COMPLETED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=AccountPaymentInstrumentV2(
                        type=PaymentInstrumentV2Type.ACCOUNT,
                        masked_account_number="<maskedAccountNumber>",
                        ifsc="<ifsc>",
                        account_holder_name="<accountHolderName>",
                        account_type="SAVINGS",
                    ),
                    rail=UpiPaymentRail(
                        utr="<utr>",
                        type=PaymentRailType.UPI,
                        upi_transaction_id="<upiTransactionId>",
                        vpa="<vpa>",
                    ),
                    split_instruments=None,
                )
            ],
        )
        assert len(responses.calls) == 1
        assert response_object == expected_order_status_obj

    @responses.activate
    def test_check_status_ppe_intent(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
          "orderId": "OMO2402281351151884090310",
          "state": "COMPLETED",
          "amount": 300,
          "expireAt": 1709108895182,
          "metaInfo": {
            "udf1": "<additional-information-1>",
            "udf2": "<additional-information-2>",
            "udf3": "<additional-information-3>",
            "udf4": "<additional-information-4>"
          },
          "paymentDetails": [
            {
              "transactionId": "OM2402281351157894090178",
              "paymentMode": "UPI_INTENT",
              "timestamp": 1709108475790,
              "amount": 300,
              "state": "FAILED",
              "errorCode": "PAYMENT_ERROR",
              "detailedErrorCode": "TXN_AUTO_FAILED",
              "responseCode": "PAYMENT_ERROR",
              "backendErrorCode": "TXN_AUTO_FAILED"
            },
            {
              "transactionId": "OM2402281351164694090252",
              "paymentMode": "PPE_INTENT",
              "timestamp": 1709108476471,
              "amount": 300,
              "state": "COMPLETED",
              "splitInstruments": [
                {
                  "instrument": {
                    "type": "WALLET"
                  },
                  "rail": {
                    "type": "PPI_WALLET"
                  },
                  "amount": 150
                },
                {
                  "instrument": {
                    "type": "EGV"
                  },
                  "rail": {
                    "type": "PPI_EGV"
                  },
                  "amount": 150
                }
              ],
              "responseCode": "PAYMENT_SUCCESS",
              "backendErrorCode": "SUCCESS"
            }
          ]
        }
        """
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        response_object = standard_checkout_client.get_order_status(
            merchant_order_id=merchant_transaction_id
        )
        expected_order_status_obj = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="OMO2402281351151884090310",
            state="COMPLETED",
            amount=300,
            expire_at=1709108895182,
            detailed_error_code=None,
            error_code=None,
            meta_info=MetaInfo(
                udf1="<additional-information-1>",
                udf2="<additional-information-2>",
                udf3="<additional-information-3>",
                udf4="<additional-information-4>",
                udf5=None,
            ),
            payment_details=[
                PaymentDetail(
                    transaction_id="OM2402281351157894090178",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1709108475790,
                    amount=300,
                    state="FAILED",
                    error_code="PAYMENT_ERROR",
                    detailed_error_code="TXN_AUTO_FAILED",
                    instrument=None,
                    rail=None,
                    split_instruments=None,
                ),
                PaymentDetail(
                    transaction_id="OM2402281351164694090252",
                    payment_mode=PgV2InstrumentType.PPE_INTENT,
                    timestamp=1709108476471,
                    amount=300,
                    state="COMPLETED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=None,
                    rail=None,
                    split_instruments=[
                        InstrumentCombo(
                            instrument=WalletPaymentInstrumentV2(
                                type=PaymentInstrumentV2Type.WALLET, wallet_id=None
                            ),
                            rail=PpiWalletPaymentRail(type=PaymentRailType.PPI_WALLET),
                            amount=150,
                        ),
                        InstrumentCombo(
                            instrument=EvgPaymentInstrumentV2(
                                type=PaymentInstrumentV2Type.EGV,
                                card_number=None,
                                program_id=None,
                            ),
                            rail=PpiEgvPaymentRail(type=PaymentRailType.PPI_EGV),
                            amount=150,
                        ),
                    ],
                ),
            ],
        )

        assert len(responses.calls) == 1
        assert response_object == expected_order_status_obj

    @responses.activate
    def test_token_failed(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{"orderId": "OMO2404191318562102488580", "state": "FAILED", "amount": 100, "expireAt": 1713685736321, "errorCode": "AUTHORIZATION_ERROR", "paymentDetails": [{"paymentMode": "TOKEN", "transactionId": "OM2404191318562112488593", "timestamp": 1713512936321, "amount": 100, "state": "FAILED", "errorCode": "AUTHORIZATION_ERROR", "rail": {"type": "PG", "transactionId": "<transactionId>", "authorizationCode": "<authorizationCode>", "serviceTransactionId": "<serviceTransactionId>"}, "instrument": {"type": "CREDIT_CARD", "bankTransactionId": "<bankTransactionId>", "bankId": "<bankId>", "arn": "<arn>", "brn": "<brn>"}}]}"""
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        response_object = standard_checkout_client.get_order_status(
            merchant_order_id=merchant_transaction_id
        )
        expected_order_status_obj = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="OMO2404191318562102488580",
            state="FAILED",
            amount=100,
            expire_at=1713685736321,
            detailed_error_code=None,
            error_code="AUTHORIZATION_ERROR",
            meta_info=None,
            payment_details=[
                PaymentDetail(
                    transaction_id="OM2404191318562112488593",
                    payment_mode=PgV2InstrumentType.TOKEN,
                    timestamp=1713512936321,
                    amount=100,
                    state="FAILED",
                    error_code="AUTHORIZATION_ERROR",
                    detailed_error_code=None,
                    instrument=CreditCardPaymentInstrumentV2(
                        type=PaymentInstrumentV2Type.CREDIT_CARD,
                        bank_transaction_id="<bankTransactionId>",
                        bank_id="<bankId>",
                        brn="<brn>",
                        arn="<arn>",
                    ),
                    rail=PgPaymentRail(
                        type=PaymentRailType.PG,
                        transaction_id="<transactionId>",
                        authorization_code="<authorizationCode>",
                        service_transaction_id="<serviceTransactionId>",
                    ),
                    split_instruments=None,
                )
            ],
        )

        assert len(responses.calls) == 1
        assert response_object == expected_order_status_obj

    @responses.activate
    def test_token_success(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{"orderId": "OMO2404191321008312488760", "state": "COMPLETED", "amount": 100, "expireAt": 1713685860940, "paymentDetails": [{"paymentMode": "TOKEN", "transactionId": "OM2404191321008312488345", "timestamp": 1713513060940, "amount": 100, "state": "COMPLETED", "rail": {"type": "PG", "transactionId": "<transactionId>", "authorizationCode": "<authorizationCode>", "serviceTransactionId": "<serviceTransactionId>"}, "instrument": {"type": "CREDIT_CARD", "bankTransactionId": "<bankTransactionId>", "bankId": "<bankId>", "arn": "<arn>", "brn": "<brn>"}}]}"""
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        response_object = standard_checkout_client.get_order_status(
            merchant_order_id=merchant_transaction_id
        )
        expected_order_status_obj = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="OMO2404191321008312488760",
            state="COMPLETED",
            amount=100,
            expire_at=1713685860940,
            detailed_error_code=None,
            error_code=None,
            meta_info=None,
            payment_details=[
                PaymentDetail(
                    transaction_id="OM2404191321008312488345",
                    payment_mode=PgV2InstrumentType.TOKEN,
                    timestamp=1713513060940,
                    amount=100,
                    state="COMPLETED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=CreditCardPaymentInstrumentV2(
                        type=PaymentInstrumentV2Type.CREDIT_CARD,
                        bank_transaction_id="<bankTransactionId>",
                        bank_id="<bankId>",
                        brn="<brn>",
                        arn="<arn>",
                    ),
                    rail=PgPaymentRail(
                        type=PaymentRailType.PG,
                        transaction_id="<transactionId>",
                        authorization_code="<authorizationCode>",
                        service_transaction_id="<serviceTransactionId>",
                    ),
                    split_instruments=None,
                )
            ],
        )

        assert len(responses.calls) == 1
        assert response_object == expected_order_status_obj

    @responses.activate
    def test_card_success(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{"orderId": "OMO2404191323224152488241", "state": "COMPLETED", "amount": 100, "expireAt": 1713686002582, "paymentDetails": [{"paymentMode": "CARD", "transactionId": "OM2404191323224162488756", "timestamp": 1713513202582, "amount": 100, "state": "COMPLETED", "rail": {"type": "PG", "transactionId": "<transactionId>", "authorizationCode": "<authorizationCode>", "serviceTransactionId": "<serviceTransactionId>"}, "instrument": {"type": "CREDIT_CARD", "bankTransactionId": "<bankTransactionId>", "bankId": "<bankId>", "arn": "<arn>", "brn": "<brn>"}}]}"""
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        response_object = standard_checkout_client.get_order_status(
            merchant_order_id=merchant_transaction_id
        )
        expected_order_status_obj = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="OMO2404191323224152488241",
            state="COMPLETED",
            amount=100,
            expire_at=1713686002582,
            detailed_error_code=None,
            error_code=None,
            meta_info=None,
            payment_details=[
                PaymentDetail(
                    transaction_id="OM2404191323224162488756",
                    payment_mode=PgV2InstrumentType.CARD,
                    timestamp=1713513202582,
                    amount=100,
                    state="COMPLETED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=CreditCardPaymentInstrumentV2(
                        type=PaymentInstrumentV2Type.CREDIT_CARD,
                        bank_transaction_id="<bankTransactionId>",
                        bank_id="<bankId>",
                        brn="<brn>",
                        arn="<arn>",
                    ),
                    rail=PgPaymentRail(
                        type=PaymentRailType.PG,
                        transaction_id="<transactionId>",
                        authorization_code="<authorizationCode>",
                        service_transaction_id="<serviceTransactionId>",
                    ),
                    split_instruments=None,
                )
            ],
        )

        assert len(responses.calls) == 1  # only 1 call to status check API
        assert response_object == expected_order_status_obj

    @responses.activate
    def test_netbanking_success(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{"orderId": "OMO2404191326420742488550", "state": "COMPLETED", "amount": 100, "expireAt": 1713686202188, "paymentDetails": [{"paymentMode": "NET_BANKING", "transactionId": "OM2404191326420752488502", "timestamp": 1713513402188, "amount": 100, "state": "COMPLETED", "rail": {"type": "PG", "transactionId": "<transactionId>", "authorizationCode": "<authorizationCode>", "serviceTransactionId": "<serviceTransactionId>"}, "instrument": {"type": "NET_BANKING", "bankTransactionId": "<bankTransactionId>", "bankId": "<bankId>", "arn": "<arn>", "brn": "<brn>"}}]}"""
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        response_object = standard_checkout_client.get_order_status(
            merchant_order_id=merchant_transaction_id
        )
        expected_order_status_obj = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="OMO2404191326420742488550",
            state="COMPLETED",
            amount=100,
            expire_at=1713686202188,
            detailed_error_code=None,
            error_code=None,
            meta_info=None,
            payment_details=[
                PaymentDetail(
                    transaction_id="OM2404191326420752488502",
                    payment_mode=PgV2InstrumentType.NET_BANKING,
                    timestamp=1713513402188,
                    amount=100,
                    state="COMPLETED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=NetBankingPaymentInstrumentV2(
                        type=PaymentInstrumentV2Type.NET_BANKING,
                        bank_transaction_id="<bankTransactionId>",
                        bank_id="<bankId>",
                        brn="<brn>",
                        arn="<arn>",
                    ),
                    rail=PgPaymentRail(
                        type=PaymentRailType.PG,
                        transaction_id="<transactionId>",
                        authorization_code="<authorizationCode>",
                        service_transaction_id="<serviceTransactionId>",
                    ),
                    split_instruments=None,
                )
            ],
        )

        assert len(responses.calls) == 1
        assert response_object == expected_order_status_obj

    @responses.activate
    def test_check_status_ppe_intent_custom(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(
            Env.SANDBOX
        ) + order_status_custom_api.format(merchant_order_id=merchant_transaction_id)
        response_string = """{
          "orderId": "OMO2402281351151884090310",
          "state": "COMPLETED",
          "amount": 300,
          "expireAt": 1709108895182,
          "metaInfo": {
            "udf1": "<additional-information-1>",
            "udf2": "<additional-information-2>",
            "udf3": "<additional-information-3>",
            "udf4": "<additional-information-4>"
          },
          "paymentDetails": [
            {
              "transactionId": "OM2402281351157894090178",
              "paymentMode": "UPI_INTENT",
              "timestamp": 1709108475790,
              "amount": 300,
              "state": "FAILED",
              "errorCode": "PAYMENT_ERROR",
              "detailedErrorCode": "TXN_AUTO_FAILED",
              "responseCode": "PAYMENT_ERROR",
              "backendErrorCode": "TXN_AUTO_FAILED"
            },
            {
              "transactionId": "OM2402281351164694090252",
              "paymentMode": "PPE_INTENT",
              "timestamp": 1709108476471,
              "amount": 300,
              "state": "COMPLETED",
              "splitInstruments": [
                {
                  "instrument": {
                    "type": "WALLET"
                  },
                  "rail": {
                    "type": "PPI_WALLET"
                  },
                  "amount": 150
                },
                {
                  "instrument": {
                    "type": "EGV"
                  },
                  "rail": {
                    "type": "PPI_EGV"
                  },
                  "amount": 150
                }
              ],
              "responseCode": "PAYMENT_SUCCESS",
              "backendErrorCode": "SUCCESS"
            }
          ]
        }
        """
        standard_checkout_client = BaseTestWithOauth.custom_checkout_client

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        response_object = standard_checkout_client.get_order_status(
            merchant_order_id=merchant_transaction_id
        )
        expected_order_status_obj = OrderStatusResponse(
            merchant_id=None,
            merchant_order_id=None,
            order_id="OMO2402281351151884090310",
            state="COMPLETED",
            amount=300,
            expire_at=1709108895182,
            detailed_error_code=None,
            error_code=None,
            meta_info=MetaInfo(
                udf1="<additional-information-1>",
                udf2="<additional-information-2>",
                udf3="<additional-information-3>",
                udf4="<additional-information-4>",
                udf5=None,
            ),
            payment_details=[
                PaymentDetail(
                    transaction_id="OM2402281351157894090178",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1709108475790,
                    amount=300,
                    state="FAILED",
                    error_code="PAYMENT_ERROR",
                    detailed_error_code="TXN_AUTO_FAILED",
                    instrument=None,
                    rail=None,
                    split_instruments=None,
                ),
                PaymentDetail(
                    transaction_id="OM2402281351164694090252",
                    payment_mode=PgV2InstrumentType.PPE_INTENT,
                    timestamp=1709108476471,
                    amount=300,
                    state="COMPLETED",
                    error_code=None,
                    detailed_error_code=None,
                    instrument=None,
                    rail=None,
                    split_instruments=[
                        InstrumentCombo(
                            instrument=WalletPaymentInstrumentV2(
                                type=PaymentInstrumentV2Type.WALLET, wallet_id=None
                            ),
                            rail=PpiWalletPaymentRail(type=PaymentRailType.PPI_WALLET),
                            amount=150,
                        ),
                        InstrumentCombo(
                            instrument=EvgPaymentInstrumentV2(
                                type=PaymentInstrumentV2Type.EGV,
                                card_number=None,
                                program_id=None,
                            ),
                            rail=PpiEgvPaymentRail(type=PaymentRailType.PPI_EGV),
                            amount=150,
                        ),
                    ],
                ),
            ],
        )

        assert len(responses.calls) == 2
        assert response_object == expected_order_status_obj

    @responses.activate
    def test_check_status_subscription(self):
        merchant_order_id = "OMOxxx"
        check_status_url = get_pg_base_url(
            Env.SANDBOX
        ) + SUBSCRIPTION_ORDER_STATUS_API.format(merchant_order_id=merchant_order_id)
        response_str = """{
                        "merchantId": "MID",
                        "merchantOrderId": "MO1708797962855",
                        "orderId": "OMO2402242336055135042802",
                        "state": "COMPLETED",
                        "amount": 200,
                        "expireAt": 170879838,
                        "paymentFlow": {
                            "type": "SUBSCRIPTION_SETUP",
                            "merchantSubscriptionId": "MS1708797962855",
                            "authWorkflowType": "TRANSACTION",
                            "amountType": "FIXED",
                            "maxAmount": 200,
                            "frequency": "ON_DEMAND",
                            "subscriptionId": "OMS2402242336054995042603"
                        },
                        "paymentDetails": [
                            {
                                "transactionId": "OM2402242336055865042862",
                                "paymentMode": "UPI_INTENT",
                                "timestamp": 1708797965588,
                                "amount": 200,
                                "state": "COMPLETED",
                                "instrument": {
                                    "type": "ACCOUNT",
                                    "maskedAccountNumber": "XXXXXXX20000",
                                    "ifsc": "AABE0000000",
                                    "accountHolderName": "AABE0000000",
                                    "accountType": "SAVINGS"
                                },
                                "rail": {
                                    "type": "UPI",
                                    "utr": "405554491450",
                                    "vpa": "<vpa>"
                                },
                                "errorCode": "PRESENT ONLY IF TRANSACTION IS FAILED",
                                "detailedErrorCode": "PRESENT ONLY IF TRANSACTION IS FAILED"
                            }
                        ]}"""

        responses.add(
            responses.GET, check_status_url, body=response_str, status=HTTPStatus.OK
        )
        expected_response = OrderStatusResponse(
            merchant_id="MID",
            merchant_order_id="MO1708797962855",
            order_id="OMO2402242336055135042802",
            state="COMPLETED",
            amount=200,
            expire_at=170879838,
            payment_flow=SubscriptionSetupPaymentFlowResponse(
                merchant_subscription_id="MS1708797962855",
                auth_workflow_type=AuthWorkflowType.TRANSACTION,
                amount_type=AmountType.FIXED,
                max_amount=200,
                frequency=Frequency.ON_DEMAND,
                subscription_id="OMS2402242336054995042603",
            ),
            payment_details=[
                PaymentDetail(
                    transaction_id="OM2402242336055865042862",
                    payment_mode=PgV2InstrumentType.UPI_INTENT,
                    timestamp=1708797965588,
                    amount=200,
                    state="COMPLETED",
                    instrument=AccountPaymentInstrumentV2(
                        type=PaymentInstrumentV2Type.ACCOUNT,
                        masked_account_number="XXXXXXX20000",
                        ifsc="AABE0000000",
                        account_holder_name="AABE0000000",
                        account_type="SAVINGS",
                    ),
                    rail=UpiPaymentRail(
                        utr="405554491450",
                        vpa="<vpa>",
                        type=PaymentRailType.UPI,
                    ),
                    error_code="PRESENT ONLY IF TRANSACTION IS FAILED",
                    detailed_error_code="PRESENT ONLY IF TRANSACTION IS FAILED",
                )
            ],
        )
        actual_response = BaseTestWithOauth.subscription_client.get_order_status(
            merchant_order_id
        )

        assert len(responses.calls) == 1
        assert actual_response == expected_response
