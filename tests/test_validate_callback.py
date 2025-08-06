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

from phonepe.sdk.pg.payments.v2.models.callback_response import CallbackResponse
from phonepe.sdk.pg.common.exceptions import PhonePeException
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.common.models.response.payment_instruments.account_payment_instrument_v2 import (
    AccountPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.credit_card_payment_instrument_v2 import (
    CreditCardPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.debit_card_payment_instrument_v2 import (
    DebitCardPaymentInstrumentV2,
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
from phonepe.sdk.pg.common.models.response.rails.upi_payment_rail import UpiPaymentRail
from phonepe.sdk.pg.env import Env, get_pg_base_url
from phonepe.sdk.pg.payments.v2.models.request.pg_v2_instrument_type import (
    PgV2InstrumentType,
)
from phonepe.sdk.pg.payments.v2.models.response.callback_data import CallbackData
from phonepe.sdk.pg.payments.v2.models.response.callback_type import CallbackType
from phonepe.sdk.pg.payments.v2.models.response.payment_detail import PaymentDetail
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import (
    ORDER_STATUS_API,
)
from phonepe.sdk.pg.subscription.v2.models.request.amount_type import AmountType
from phonepe.sdk.pg.subscription.v2.models.request.auth_workflow_type import (
    AuthWorkflowType,
)
from phonepe.sdk.pg.subscription.v2.models.request.frequency import Frequency
from phonepe.sdk.pg.subscription.v2.models.request.redemption_retry_strategy import (
    RedemptionRetryStrategy,
)
from phonepe.sdk.pg.subscription.v2.models.response.subscription_redemption_payment_flow_response import (
    SubscriptionRedemptionPaymentFlowResponse,
)
from phonepe.sdk.pg.subscription.v2.models.response.subscription_setup_payment_flow_response import (
    SubscriptionSetupPaymentFlowResponse,
)
from tests.base_test_with_oauth import BaseTestWithOauth


class TestValidateCallback(BaseTestWithOauth):

    @responses.activate
    def test_validate_CHECKOUT_TRANSACTION_ATTEMPT_FAILED(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """
        {
          "event": "checkout.transaction.attempt.failed",
          "type": "CHECKOUT_TRANSACTION_ATTEMPT_FAILED",
          "payload": {
            "merchantId": "MID",
            "merchantOrderId": "MO1af83fb6",
            "orderId": "OMO2403041556072639596105",
            "state": "PENDING",
            "amount": 10001,
            "expireAt": 1709548387262,
            "errorCode": "PAYMENT_ERROR",
            "detailedErrorCode": "TXN_AUTO_FAILED",
            "metaInfo": {
              "udf1": "dummy1"
            },
            "paymentDetails": [
              {
                "transactionId": "OM2403041556097829596189",
                "paymentMode": "UPI_INTENT",
                "timestamp": 1709547969783,
                "amount": 10001,
                "state": "FAILED",
                "errorCode": "PAYMENT_ERROR",
                "detailedErrorCode": "TXN_AUTO_FAILED"
              }
            ]
          }
        }"""

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )

        callback_response_object = CallbackResponse(
            event="checkout.transaction.attempt.failed",
            type=CallbackType.CHECKOUT_TRANSACTION_ATTEMPT_FAILED,
            payload=CallbackData(
                order_id="OMO2403041556072639596105",
                merchant_id="MID",
                merchant_order_id="MO1af83fb6",
                state="PENDING",
                amount=10001,
                expire_at=1709548387262,
                error_code="PAYMENT_ERROR",
                detailed_error_code="TXN_AUTO_FAILED",
                meta_info=MetaInfo(
                    udf1="dummy1", udf2=None, udf3=None, udf4=None, udf5=None
                ),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM2403041556097829596189",
                        payment_mode=PgV2InstrumentType.UPI_INTENT,
                        timestamp=1709547969783,
                        amount=10001,
                        state="FAILED",
                        error_code="PAYMENT_ERROR",
                        detailed_error_code="TXN_AUTO_FAILED",
                        instrument=None,
                        rail=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_ORDER_COMPLETED_via_debit_card(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
          "event" : "pg.order.completed",
          "type": "PG_ORDER_COMPLETED",
          "payload": {
            "orderId": "OMOxx",
            "merchantId": "merchantId",
            "merchantOrderId": "merchantOrderId",
            "state": "EXPIRED",
            "amount": 10000,
            "expireAt": 1291391291,
            "metaInfo": {
              "udf1": "",
              "udf2": "",
              "udf3": "",
              "udf4": "",
              "udf5": ""
            },
            "paymentDetails": [
              {
                "paymentMode": "UPI_COLLECT",
                "timestamp": 12121212,
                "amount": 10000,
                "transactionId": "OM12333",
                "state": "FAILED",
                "errorCode": "AUTHORIZATION_ERROR",
                "detailedErrorCode": "ZM",
                "rail": {
                  "type": "PPI_EGV"
                },
                "instrument": {
                  "type": "DEBIT_CARD",
                  "bankTransactionId": "bankTransactionId",
                  "bankId": "bankId",
                  "brn": "brn",
                  "arn": "arn"
                }
              }
            ]
          }
        }
        """

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )

        callback_response_object = CallbackResponse(
            event="pg.order.completed",
            type=CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id="OMOxx",
                merchant_order_id="merchantOrderId",
                original_merchant_order_id=None,
                refund_id=None,
                merchant_refund_id=None,
                state="EXPIRED",
                amount=10000,
                expire_at=1291391291,
                error_code=None,
                detailed_error_code=None,
                meta_info=MetaInfo(udf1="", udf2="", udf3="", udf4="", udf5=""),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM12333",
                        payment_mode=PgV2InstrumentType.UPI_COLLECT,
                        timestamp=12121212,
                        amount=10000,
                        state="FAILED",
                        error_code="AUTHORIZATION_ERROR",
                        detailed_error_code="ZM",
                        instrument=DebitCardPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.DEBIT_CARD,
                            bank_transaction_id="bankTransactionId",
                            bank_id="bankId",
                            brn="brn",
                            arn="arn",
                        ),
                        rail=PpiEgvPaymentRail(type=PaymentRailType.PPI_EGV),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_ORDER_COMPLETED_via_credit_card(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
          "event" : "pg.order.completed",
          "type": "PG_ORDER_COMPLETED",
          "payload": {
            "orderId": "OMOxx",
            "merchantId": "merchantId",
            "merchantOrderId": "merchantOrderId",
            "state": "EXPIRED",
            "amount": 10000,
            "expireAt": 1291391291,
            "metaInfo": {
              "udf1": "",
              "udf2": "",
              "udf3": "",
              "udf4": "",
              "udf5": ""
            },
            "paymentDetails": [
              {
                "paymentMode": "UPI_COLLECT",
                "timestamp": 12121212,
                "amount": 10000,
                "transactionId": "OM12333",
                "state": "FAILED",
                "errorCode": "AUTHORIZATION_ERROR",
                "detailedErrorCode": "ZM",
                "rail": {
                  "type": "PPI_EGV"
                },
                "instrument": {
                  "type": "CREDIT_CARD",
                  "bankTransactionId": "bankTransactionId",
                  "bankId": "bankId",
                  "brn": "brn",
                  "arn": "arn"
                }
              }
            ]
          }
        }
        """

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )

        callback_response_object = CallbackResponse(
            event="pg.order.completed",
            type = CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id="OMOxx",
                merchant_order_id="merchantOrderId",
                original_merchant_order_id=None,
                refund_id=None,
                merchant_refund_id=None,
                state="EXPIRED",
                amount=10000,
                expire_at=1291391291,
                error_code=None,
                detailed_error_code=None,
                meta_info=MetaInfo(udf1="", udf2="", udf3="", udf4="", udf5=""),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM12333",
                        payment_mode=PgV2InstrumentType.UPI_COLLECT,
                        timestamp=12121212,
                        amount=10000,
                        state="FAILED",
                        error_code="AUTHORIZATION_ERROR",
                        detailed_error_code="ZM",
                        instrument=CreditCardPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.CREDIT_CARD,
                            bank_transaction_id="bankTransactionId",
                            bank_id="bankId",
                            brn="brn",
                            arn="arn",
                        ),
                        rail=PpiEgvPaymentRail(type=PaymentRailType.PPI_EGV),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_ORDER_COMPLETED_via_evg(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
          "event" : "pg.order.completed",
          "type": "PG_ORDER_COMPLETED",
          "payload": {
            "orderId": "OMOxx",
            "merchantId": "merchantId",
            "merchantOrderId": "merchantOrderId",
            "state": "EXPIRED",
            "amount": 10000,
            "expireAt": 1291391291,
            "metaInfo": {
              "udf1": "",
              "udf2": "",
              "udf3": "",
              "udf4": "",
              "udf5": ""
            },
            "paymentDetails": [
              {
                "paymentMode": "UPI_COLLECT",
                "timestamp": 12121212,
                "amount": 10000,
                "transactionId": "OM12333",
                "state": "FAILED",
                "errorCode": "AUTHORIZATION_ERROR",
                "detailedErrorCode": "ZM",
                "rail": {
                  "type": "PPI_EGV"
                },
                "instrument": {
                  "type": "EGV",
                  "cardNumber": "cardNumber",
                  "programId": "programId"
                }
              }
            ]
          }
        }
        """

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )

        callback_response_object = CallbackResponse(
            event="pg.order.completed",
            type = CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id="OMOxx",
                merchant_order_id="merchantOrderId",
                original_merchant_order_id=None,
                refund_id=None,
                merchant_refund_id=None,
                state="EXPIRED",
                amount=10000,
                expire_at=1291391291,
                error_code=None,
                detailed_error_code=None,
                meta_info=MetaInfo(udf1="", udf2="", udf3="", udf4="", udf5=""),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM12333",
                        payment_mode=PgV2InstrumentType.UPI_COLLECT,
                        timestamp=12121212,
                        amount=10000,
                        state="FAILED",
                        error_code="AUTHORIZATION_ERROR",
                        detailed_error_code="ZM",
                        instrument=EvgPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.EGV,
                            card_number="cardNumber",
                            program_id="programId",
                        ),
                        rail=PpiEgvPaymentRail(type=PaymentRailType.PPI_EGV),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_ORDER_COMPLETED_via_wallet(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )

        response_string = """{
          "event" : "pg.order.completed",
          "type": "PG_ORDER_COMPLETED",
          "payload": {
            "orderId": "OMOxx",
            "merchantId": "merchantId",
            "merchantOrderId": "merchantOrderId",
            "state": "EXPIRED",
            "amount": 10000,
            "expireAt": 1291391291,
            "metaInfo": {
              "udf1": "",
              "udf2": "",
              "udf3": "",
              "udf4": "",
              "udf5": ""
            },
            "paymentDetails": [
              {
                "paymentMode": "UPI_COLLECT",
                "timestamp": 12121212,
                "amount": 10000,
                "transactionId": "OM12333",
                "state": "FAILED",
                "errorCode": "AUTHORIZATION_ERROR",
                "detailedErrorCode": "ZM",
                "rail": {
                  "type": "PPI_EGV"
                },
                "instrument": {
                  "type": "WALLET",
                  "walletId": "walletId"
                }
              }
            ]
          }
        }
        """

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        callback_response_object = CallbackResponse(
            event="pg.order.completed",
            type = CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id="OMOxx",
                merchant_order_id="merchantOrderId",
                original_merchant_order_id=None,
                refund_id=None,
                merchant_refund_id=None,
                state="EXPIRED",
                amount=10000,
                expire_at=1291391291,
                error_code=None,
                detailed_error_code=None,
                meta_info=MetaInfo(udf1="", udf2="", udf3="", udf4="", udf5=""),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM12333",
                        payment_mode=PgV2InstrumentType.UPI_COLLECT,
                        timestamp=12121212,
                        amount=10000,
                        state="FAILED",
                        error_code="AUTHORIZATION_ERROR",
                        detailed_error_code="ZM",
                        instrument=WalletPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.WALLET, wallet_id="walletId"
                        ),
                        rail=PpiEgvPaymentRail(type=PaymentRailType.PPI_EGV),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_ORDER_COMPLETED_via_ppi_evg(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )

        response_string = """{
          "event" : "pg.order.completed",
          "type": "PG_ORDER_COMPLETED",
          "payload": {
            "orderId": "OMOxx",
            "merchantId": "merchantId",
            "merchantOrderId": "merchantOrderId",
            "state": "EXPIRED",
            "amount": 10000,
            "expireAt": 1291391291,
            "metaInfo": {
              "udf1": "",
              "udf2": "",
              "udf3": "",
              "udf4": "",
              "udf5": ""
            },
            "paymentDetails": [
              {
                "paymentMode": "UPI_COLLECT",
                "timestamp": 12121212,
                "amount": 10000,
                "transactionId": "OM12333",
                "state": "FAILED",
                "errorCode": "AUTHORIZATION_ERROR",
                "detailedErrorCode": "ZM",
                "rail": {
                  "type": "PPI_EGV"
                },
                "instrument": {
                  "type": "ACCOUNT",
                  "accountType": "SAVINGS",
                  "maskedAccountNumber": "121212121212"
                }
              }
            ]
          }
        }
        """

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        callback_response_object = CallbackResponse(
            event="pg.order.completed",
            type=CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id="OMOxx",
                merchant_order_id="merchantOrderId",
                original_merchant_order_id=None,
                refund_id=None,
                merchant_refund_id=None,
                state="EXPIRED",
                amount=10000,
                expire_at=1291391291,
                error_code=None,
                detailed_error_code=None,
                meta_info=MetaInfo(udf1="", udf2="", udf3="", udf4="", udf5=""),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM12333",
                        payment_mode=PgV2InstrumentType.UPI_COLLECT,
                        timestamp=12121212,
                        amount=10000,
                        state="FAILED",
                        error_code="AUTHORIZATION_ERROR",
                        detailed_error_code="ZM",
                        instrument=AccountPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.ACCOUNT,
                            masked_account_number="121212121212",
                            ifsc=None,
                            account_holder_name=None,
                            account_type="SAVINGS",
                        ),
                        rail=PpiEgvPaymentRail(type=PaymentRailType.PPI_EGV),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_ORDER_COMPLETED_via_pg(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )

        response_string = """{
          "event" : "pg.order.completed",
          "type": "PG_ORDER_COMPLETED",
          "payload": {
            "orderId": "OMOxx",
            "merchantId": "merchantId",
            "merchantOrderId": "merchantOrderId",
            "state": "EXPIRED",
            "amount": 10000,
            "expireAt": 1291391291,
            "metaInfo": {
              "udf1": "",
              "udf2": "",
              "udf3": "",
              "udf4": "",
              "udf5": ""
            },
            "paymentDetails": [
              {
                "paymentMode": "UPI_COLLECT",
                "timestamp": 12121212,
                "amount": 10000,
                "transactionId": "OM12333",
                "state": "FAILED",
                "errorCode": "AUTHORIZATION_ERROR",
                "detailedErrorCode": "ZM",
                "rail": {
                  "type": "PG",
                  "authorizationCode": "authorization",
                  "serviceTransactionId": "serviceTransactionId",
                  "transactionId": "transactionId"
                },
                "instrument": {
                  "type": "ACCOUNT",
                  "accountType": "SAVINGS",
                  "maskedAccountNumber": "121212121212"
                }
              }
            ]
          }
        }
        """

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        callback_response_object = CallbackResponse(
            event="pg.order.completed",
            type=CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id="OMOxx",
                merchant_order_id="merchantOrderId",
                original_merchant_order_id=None,
                refund_id=None,
                merchant_refund_id=None,
                state="EXPIRED",
                amount=10000,
                expire_at=1291391291,
                error_code=None,
                detailed_error_code=None,
                meta_info=MetaInfo(udf1="", udf2="", udf3="", udf4="", udf5=""),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM12333",
                        payment_mode=PgV2InstrumentType.UPI_COLLECT,
                        timestamp=12121212,
                        amount=10000,
                        state="FAILED",
                        error_code="AUTHORIZATION_ERROR",
                        detailed_error_code="ZM",
                        instrument=AccountPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.ACCOUNT,
                            masked_account_number="121212121212",
                            ifsc=None,
                            account_holder_name=None,
                            account_type="SAVINGS",
                        ),
                        rail=PgPaymentRail(
                            type=PaymentRailType.PG,
                            transaction_id="transactionId",
                            authorization_code="authorization",
                            service_transaction_id="serviceTransactionId",
                        ),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_CHECKOUT_TRANSACTION_ATTEMPT_FAILED_2(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
          "event": "checkout.transaction.attempt.failed",
          "type": "CHECKOUT_TRANSACTION_ATTEMPT_FAILED",
          "payload": {
            "merchantId": "MID",
            "merchantOrderId": "MOID01",
            "orderId": "OMO2403041625203649596290",
            "state": "PENDING",
            "amount": 10001,
            "expireAt": 1709550140362,
            "errorCode": "PAYMENT_ERROR",
            "detailedErrorCode": "TXN_FAILED",
            "metaInfo": {
              "udf1": "dummy1"
            },
            "paymentDetails": [
              {
                "transactionId": "OM2403041625351229596788",
                "paymentMode": "NET_BANKING",
                "timestamp": 1709549735123,
                "amount": 10001,
                "state": "FAILED",
                "errorCode": "PAYMENT_ERROR",
                "detailedErrorCode": "TXN_FAILED",
                "instrument": {
                  "type": "NET_BANKING",
                  "bankId": "ABCD"
                },
                "rail": {
                  "type": "PG",
                  "transactionId": "E35244128",
                  "serviceTransactionId": "PG123"
                }
              }
            ]
          }
        }"""

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )

        expected_callback_response = CallbackResponse(
            event="checkout.transaction.attempt.failed",
            type=CallbackType.CHECKOUT_TRANSACTION_ATTEMPT_FAILED,
            payload=CallbackData(
                order_id="OMO2403041625203649596290",
                merchant_id="MID",
                merchant_order_id="MOID01",
                state="PENDING",
                amount=10001,
                expire_at=1709550140362,
                error_code="PAYMENT_ERROR",
                detailed_error_code="TXN_FAILED",
                meta_info=MetaInfo(
                    udf1="dummy1", udf2=None, udf3=None, udf4=None, udf5=None
                ),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM2403041625351229596788",
                        payment_mode=PgV2InstrumentType.NET_BANKING,
                        timestamp=1709549735123,
                        amount=10001,
                        state="FAILED",
                        error_code="PAYMENT_ERROR",
                        detailed_error_code="TXN_FAILED",
                        instrument=NetBankingPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.NET_BANKING,
                            bank_transaction_id=None,
                            bank_id="ABCD",
                            brn=None,
                            arn=None,
                        ),
                        rail=PgPaymentRail(
                            type=PaymentRailType.PG,
                            transaction_id="E35244128",
                            service_transaction_id="PG123",
                        ),
                    )
                ],
            ),
        )

        assert actual_callback_response == expected_callback_response

    @responses.activate
    def test_validate_PG_ORDER_FAILED(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """
        {
          "event" : "pg.order.completed",
          "type": "PG_ORDER_COMPLETED",
          "payload": {
            "merchantId": "MID",
            "merchantOrderId": "MO1af83fb6",
            "orderId": "OMO2403041556072639596105",
            "state": "PENDING",
            "amount": 10001,
            "expireAt": 1709548387262,
            "errorCode": "PAYMENT_ERROR",
            "detailedErrorCode": "TXN_AUTO_FAILED",
            "metaInfo": {
              "udf1": "dummy1"
            },
            "paymentDetails": [
              {
                "transactionId": "OM2403041556097829596189",
                "paymentMode": "UPI_INTENT",
                "timestamp": 1709547969783,
                "amount": 10001,
                "state": "FAILED",
                "errorCode": "PAYMENT_ERROR",
                "detailedErrorCode": "TXN_AUTO_FAILED"
              }
            ]
          }
        }"""

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )

        callback_response_object = CallbackResponse(
            event="pg.order.completed",
            type=CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                order_id="OMO2403041556072639596105",
                merchant_id="MID",
                merchant_order_id="MO1af83fb6",
                state="PENDING",
                amount=10001,
                expire_at=1709548387262,
                error_code="PAYMENT_ERROR",
                detailed_error_code="TXN_AUTO_FAILED",
                meta_info=MetaInfo(
                    udf1="dummy1", udf2=None, udf3=None, udf4=None, udf5=None
                ),
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM2403041556097829596189",
                        payment_mode=PgV2InstrumentType.UPI_INTENT,
                        timestamp=1709547969783,
                        amount=10001,
                        state="FAILED",
                        error_code="PAYMENT_ERROR",
                        detailed_error_code="TXN_AUTO_FAILED",
                        instrument=None,
                        rail=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_ORDER_COMPLETED(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
                  "event" : "pg.order.completed",
                  "type": "PG_ORDER_COMPLETED",
                  "payload": {
                    "merchantId": "merchantId",
                    "merchantOrderId": "merchantOrderId",
                    "orderId": "orderId",
                    "state": "COMPLETED",
                    "amount": 123,
                    "expireAt": 123,
                    "metaInfo": {},
                    "paymentDetails": [
                      {
                        "paymentMode": "UPI_QR",
                        "transactionId": "transactionId",
                        "timestamp": 123,
                        "amount": 123,
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
                          "accountNumber": "<accountNumber>",
                          "ifsc": "<ifsc>"
                        }
                      }
                    ]
                  }
                }"""

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        callback_response_object = CallbackResponse(
            event="pg.order.completed",
            type=CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id="orderId",
                merchant_order_id="merchantOrderId",
                original_merchant_order_id=None,
                refund_id=None,
                merchant_refund_id=None,
                state="COMPLETED",
                amount=123,
                expire_at=123,
                error_code=None,
                detailed_error_code=None,
                meta_info=MetaInfo(
                    udf1=None, udf2=None, udf3=None, udf4=None, udf5=None
                ),
                payment_details=[
                    PaymentDetail(
                        transaction_id="transactionId",
                        payment_mode=PgV2InstrumentType.UPI_QR,
                        timestamp=123,
                        amount=123,
                        state="COMPLETED",
                        error_code=None,
                        detailed_error_code=None,
                        instrument=AccountPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.ACCOUNT,
                            masked_account_number="<maskedAccountNumber>",
                            ifsc="<ifsc>",
                            account_holder_name=None,
                            account_type="SAVINGS",
                        ),
                        rail=UpiPaymentRail(
                            type=PaymentRailType.UPI,
                            utr="<utr>",
                            upi_transaction_id="<upiTransactionId>",
                            vpa="<vpa>",
                        ),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_REFUND_ACCEPTED(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
            "event": "pg.refund.accepted",
            "type" : "PG_REFUND_ACCEPTED",
            "payload": {
              "merchantId" : "merchantId",
              "merchantRefundId" : "merchantRefundId",
              "originalMerchantOrderId": "originalMerchantOrderId",
              "amount": 10,
              "state": "CONFIRMED",
              "paymentDetails": [
                {
                  "paymentMode": "UPI_QR",
                  "timestamp": 123,
                  "amount": 123,
                  "transactionId": "transactionId",
                  "state": "CONFIRMED"
                }
              ]
            }
          }"""

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )

        callback_response_object = CallbackResponse(
            event="pg.refund.accepted",
            type = CallbackType.PG_REFUND_ACCEPTED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id=None,
                merchant_order_id=None,
                original_merchant_order_id="originalMerchantOrderId",
                refund_id=None,
                merchant_refund_id="merchantRefundId",
                state="CONFIRMED",
                amount=10,
                expire_at=None,
                error_code=None,
                detailed_error_code=None,
                meta_info=None,
                payment_details=[
                    PaymentDetail(
                        transaction_id="transactionId",
                        payment_mode=PgV2InstrumentType.UPI_QR,
                        timestamp=123,
                        amount=123,
                        state="CONFIRMED",
                        error_code=None,
                        detailed_error_code=None,
                        instrument=None,
                        rail=None,
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_validate_PG_REFUND_COMPLETED(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id
        )
        response_string = """{
                    "event": "pg.refund.completed",
                    "type" : "PG_REFUND_COMPLETED",
                    "payload": {
                      "merchantId" : "merchantId",
                      "merchantRefundId" : "merchantRefundId",
                      "originalMerchantOrderId" : "originalMerchantOrderId",
                      "amount": 123,
                      "state": "COMPLETED",
                      "paymentDetails": [
                        {
                          "paymentMode": "UPI_QR",
                          "timestamp": 123,
                          "amount": 123,
                          "transactionId": "tid",
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
                  }"""

        actual_callback_response = BaseTestWithOauth.standard_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        responses.add(
            responses.GET,
            check_status_url,
            status=200,
            body="",
            json=json.loads(response_string),
        )
        callback_response_object = CallbackResponse(
            event="pg.refund.completed",
            type= CallbackType.PG_REFUND_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id=None,
                merchant_order_id=None,
                original_merchant_order_id="originalMerchantOrderId",
                refund_id=None,
                merchant_refund_id="merchantRefundId",
                state="COMPLETED",
                amount=123,
                expire_at=None,
                error_code=None,
                detailed_error_code=None,
                meta_info=None,
                payment_details=[
                    PaymentDetail(
                        transaction_id="tid",
                        payment_mode=PgV2InstrumentType.UPI_QR,
                        timestamp=123,
                        amount=123,
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
                            type=PaymentRailType.UPI,
                            utr="<utr>",
                            upi_transaction_id="<upiTransactionId>",
                            vpa="<vpa>",
                        ),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_invalid_hash(self):
        response_string = """{
          "event": "checkout.transaction.attempt.failed",
          "type" : "CHECKOUT_TRANSACTION_ATTEMPT_FAILED",
          "payload": {
            "merchantId": "MID",
            "merchantOrderId": "MOID01",
            "orderId": "OMO2403041625203649596290",
            "state": "PENDING",
            "amount": 10001,
            "expireAt": 1709550140362,
            "errorCode": "PAYMENT_ERROR",
            "detailedErrorCode": "TXN_FAILED",
            "metaInfo": {
              "udf1": "dummy1"
            },
            "paymentDetails": [
              {
                "transactionId": "OM2403041625351229596788",
                "paymentMode": "NET_BANKING",
                "timestamp": 1709549735123,
                "amount": 10001,
                "state": "FAILED",
                "errorCode": "PAYMENT_ERROR",
                "detailedErrorCode": "TXN_FAILED",
                "instrument": {
                  "type": "NET_BANKING",
                  "bankId": "ABCD"
                },
                "rail": {
                  "type": "PG",
                  "transactionId": "E35244128",
                  "serviceTransactionId": "PG123"
                }
              }
            ]
          }
        }"""

        self.assertRaises(
            PhonePeException,
            BaseTestWithOauth.standard_checkout_client.validate_callback,
            "username",
            "password",
            response_string,
            "bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

    @responses.activate
    def test_validate_PG_REFUND_COMPLETED_custom(self):
        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        response_string = """{
                    "event": "pg.refund.completed",
                    "type": "PG_REFUND_COMPLETED",
                    "payload": {
                      "merchantId" : "merchantId",
                      "merchantRefundId" : "merchantRefundId",
                      "originalMerchantOrderId" : "originalMerchantOrderId",
                      "amount": 123,
                      "state": "COMPLETED",
                      "paymentDetails": [
                        {
                          "paymentMode": "UPI_QR",
                          "timestamp": 123,
                          "amount": 123,
                          "transactionId": "tid",
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
                  }"""

        actual_callback_response = BaseTestWithOauth.custom_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        callback_response_object = CallbackResponse(
            event="pg.refund.completed",
            type=CallbackType.PG_REFUND_COMPLETED,
            payload=CallbackData(
                merchant_id="merchantId",
                order_id=None,
                merchant_order_id=None,
                original_merchant_order_id="originalMerchantOrderId",
                refund_id=None,
                merchant_refund_id="merchantRefundId",
                state="COMPLETED",
                amount=123,
                expire_at=None,
                error_code=None,
                detailed_error_code=None,
                meta_info=None,
                payment_details=[
                    PaymentDetail(
                        transaction_id="tid",
                        payment_mode=PgV2InstrumentType.UPI_QR,
                        timestamp=123,
                        amount=123,
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
                            type=PaymentRailType.UPI,
                            utr="<utr>",
                            upi_transaction_id="<upiTransactionId>",
                            vpa="<vpa>",
                        ),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert callback_response_object == actual_callback_response

    @responses.activate
    def test_with_fee_amount(self):
        # prepare expected request
        response_string = """{
                   "event" : "pg.order.completed",
                   "type": "PG_ORDER_COMPLETED",
                   "payload":{
                      "orderId":"OMO2404181217419881571577",
                      "merchantId":"MID",
                      "merchantOrderId":"OMPL2404181217419741571575",
                      "state":"COMPLETED",
                      "amount":100,
                      "expireAt":1716056999999,
                      "paymentDetails":[
                         {
                            "transactionId":"OM2404231554133859287908",
                            "paymentMode":"UPI_INTENT",
                            "timestamp":1713867853386,
                            "amount":100,
                            "payableAmount":100,
                            "feeAmount":0,
                            "state":"COMPLETED",
                            "instrument":{
                               "type":"ACCOUNT",
                               "maskedAccountNumber":"653034XXXXXXXX81",
                               "ifsc":"UTIB0AXISCC",
                               "accountType":"CREDIT"
                            },
                            "rail":{
                               "type":"UPI",
                               "utr":"411445977270",
                               "upiTransactionId":"xxxxupitransactionId",
                               "vpa":"<vpa>"
                            }
                         }
                      ]
                   }
                }"""

        actual_callback_response = BaseTestWithOauth.custom_checkout_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )

        expected_response = CallbackResponse(
            event="pg.order.completed",
            type=CallbackType.PG_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="MID",
                order_id="OMO2404181217419881571577",
                merchant_order_id="OMPL2404181217419741571575",
                original_merchant_order_id=None,
                refund_id=None,
                merchant_refund_id=None,
                state="COMPLETED",
                amount=100,
                expire_at=1716056999999,
                error_code=None,
                detailed_error_code=None,
                meta_info=None,
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM2404231554133859287908",
                        payment_mode=PgV2InstrumentType.UPI_INTENT,
                        timestamp=1713867853386,
                        payable_amount=100,
                        fee_amount=0,
                        amount=100,
                        state="COMPLETED",
                        error_code=None,
                        detailed_error_code=None,
                        instrument=AccountPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.ACCOUNT,
                            masked_account_number="653034XXXXXXXX81",
                            ifsc="UTIB0AXISCC",
                            account_holder_name=None,
                            account_type="CREDIT",
                        ),
                        rail=UpiPaymentRail(
                            type=PaymentRailType.UPI,
                            utr="411445977270",
                            upi_transaction_id="xxxxupitransactionId",
                            vpa="<vpa>",
                        ),
                        split_instruments=None,
                    )
                ],
            ),
        )

        assert actual_callback_response == expected_response

    @responses.activate
    def test_validate_callback_subscription(self):
        response_string = """
                {
                   "event" : "subscription.cancelled",
                   "type": "SUBSCRIPTION_CANCELLED",
                   "payload":{
                      "merchantSubscriptionId":"MS1708797962855",
                      "subscriptionId":"OMS2402242336054995042603",
                      "state":"CANCELLED",
                      "authWorkflowType":"TRANSACTION",
                      "amountType":"FIXED",
                      "maxAmount":200,
                      "frequency":"ON_DEMAND",
                      "expireAt":1737278524000,
                      "pauseStartDate":1708798426196,
                      "pauseEndDate":1708885799000
                   }
                }"""

        actual_callback_response = BaseTestWithOauth.subscription_client.validate_callback(
            username="username",
            password="password",
            callback_response_data=response_string,
            callback_header_data="bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
        )
        expected_response = CallbackResponse(
            event="subscription.cancelled",
            type = CallbackType.SUBSCRIPTION_CANCELLED,
            payload=CallbackData(
                merchant_subscription_id="MS1708797962855",
                subscription_id="OMS2402242336054995042603",
                state="CANCELLED",
                auth_workflow_type=AuthWorkflowType.TRANSACTION,
                amount_type=AmountType.FIXED,
                max_amount=200,
                frequency=Frequency.ON_DEMAND,
                expire_at=1737278524000,
                pause_start_date=1708798426196,
                pause_end_date=1708885799000,
            ),
        )

        assert actual_callback_response == expected_response

    @responses.activate
    def test_subscription_setup_success(self):
        response_string = """{
              "event": "subscription.setup.order.completed",
              "type": "SUBSCRIPTION_SETUP_ORDER_COMPLETED",
              "payload": {
                "merchantId": "MID",
                "merchantOrderId": "MO1af83fb6",
                "orderId": "OMO2403041556072639596105",
                "state": "COMPLETED",
                "amount": 10001,
                "expireAt": 1709548387262,
                "paymentFlow": {
                  "type": "SUBSCRIPTION_SETUP",
                  "merchantSubscriptionId": "MS1af83fb6",
                  "authWorkflowType": "TRANSACTION",
                  "amountType": "FIXED",
                  "maxAmount": 10001,
                  "frequency": "ON_DEMAND",
                  "subscriptionId": "OMS2403041556097829596189"
                },
                "paymentDetails": [
                  {
                    "transactionId": "OM2403041556072639596105",
                    "paymentMode": "UPI_INTENT",
                    "timestamp": 1709548387262,
                    "amount": 10001,
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
                      "vpa": "<vpa>",
                      "upi_transaction_id": "d519347eb2374125bcad6e69a42cc13b@ybl"
                    }
                  }
                ]
              }
        }"""

        actual_response = BaseTestWithOauth.subscription_client.validate_callback(
            "username",
            "password",
            "bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
            response_string,
        )
        expected = CallbackResponse(
            event="subscription.setup.order.completed",
            type = CallbackType.SUBSCRIPTION_SETUP_ORDER_COMPLETED,
            payload=CallbackData(
                merchant_id="MID",
                merchant_order_id="MO1af83fb6",
                order_id="OMO2403041556072639596105",
                state="COMPLETED",
                amount=10001,
                expire_at=1709548387262,
                payment_flow=SubscriptionSetupPaymentFlowResponse(
                    merchant_subscription_id="MS1af83fb6",
                    auth_workflow_type=AuthWorkflowType.TRANSACTION,
                    amount_type=AmountType.FIXED,
                    max_amount=10001,
                    frequency=Frequency.ON_DEMAND,
                    subscription_id="OMS2403041556097829596189",
                ),
                error_code=None,
                detailed_error_code=None,
                payment_details=[
                    PaymentDetail(
                        transaction_id="OM2403041556072639596105",
                        payment_mode=PgV2InstrumentType.UPI_INTENT,
                        timestamp=1709548387262,
                        amount=10001,
                        state="COMPLETED",
                        instrument=AccountPaymentInstrumentV2(
                            type=PaymentInstrumentV2Type.ACCOUNT,
                            masked_account_number="XXXXXXX20000",
                            ifsc="AABE0000000",
                            account_holder_name="AABE0000000",
                            account_type="SAVINGS",
                        ),
                        rail=UpiPaymentRail(
                            type=PaymentRailType.UPI,
                            utr="405554491450",
                            vpa="<vpa>",
                            upi_transaction_id="d519347eb2374125bcad6e69a42cc13b@ybl",
                        ),
                        error_code=None,
                        detailed_error_code=None,
                    )
                ],
            ),
        )
        self.assertEqual(expected, actual_response)

    @responses.activate
    def test_notify_validate(self):
        response_string = """{
            "event" : "subscription.notification.completed",
            "type": "SUBSCRIPTION_NOTIFICATION_COMPLETED",
            "payload": {
                "merchantId": "TESTMID",
                "merchantOrderId": "MO1708797962855",
                "orderId": "OMO12344",
                "amount": 100,
                "state": "NOTIFIED",
                "expireAt": 1620891733101,
                "metaInfo": {
                    "udf1": "<some meta info of max length 256>",
                    "udf2": "<some meta info of max length 256>",
                    "udf3": "<some meta info of max length 256>",
                    "udf4": "<some meta info of max length 256>"
                },
                "paymentFlow": {
                    "type": "SUBSCRIPTION_REDEMPTION",
                    "merchantSubscriptionId": "MS121312",
                    "redemptionRetryStrategy": "CUSTOM",
                    "autoDebit": true,
                    "validAfter": 1628229131000,
                    "validUpto": 1628574731000,
                    "notifiedAt": 1622539751586
                }
            }
        }"""

        actual = BaseTestWithOauth.subscription_client.validate_callback(
            "username",
            "password",
            "bc842c31a9e54efe320d30d948be61291f3ceee4766e36ab25fa65243cd76e0e",
            response_string,
        )
        expected = CallbackResponse(
            event="subscription.notification.completed",
            type = CallbackType.SUBSCRIPTION_NOTIFICATION_COMPLETED,
            payload=CallbackData(
                merchant_id="TESTMID",
                merchant_order_id="MO1708797962855",
                order_id="OMO12344",
                state="NOTIFIED",
                amount=100,
                expire_at=1620891733101,
                meta_info=MetaInfo(
                    udf1="<some meta info of max length 256>",
                    udf2="<some meta info of max length 256>",
                    udf3="<some meta info of max length 256>",
                    udf4="<some meta info of max length 256>",
                ),
                payment_flow=SubscriptionRedemptionPaymentFlowResponse(
                    merchant_subscription_id="MS121312",
                    redemption_retry_strategy=RedemptionRetryStrategy.CUSTOM,
                    auto_debit=True,
                    valid_after=1628229131000,
                    valid_upto=1628574731000,
                    notified_at=1622539751586,
                ),
            ),
        )
        self.assertEqual(actual, expected)
