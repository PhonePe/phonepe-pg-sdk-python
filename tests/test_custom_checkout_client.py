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
from time import time, sleep
from unittest import TestCase
from unittest.mock import patch

import responses
from responses import matchers

import phonepe
from phonepe.sdk.pg.common.exceptions import UnauthorizedAccess
from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.common.token_handler.token_service import TokenService
from phonepe.sdk.pg.common.models.response.order_status_response import OrderStatusResponse

from phonepe.sdk.pg.env import Env, get_pg_base_url, get_oauth_base_url
from phonepe.sdk.pg.payments.v2.custom_checkout.custom_checkout_constants import ORDER_STATUS_API
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.payments.v2.models.request.pg_v2_instrument_type import PgV2InstrumentType
from phonepe.sdk.pg.payments.v2.models.response.payment_detail import PaymentDetail
from phonepe.sdk.pg.common.models.response.payment_instruments.account_payment_instrument_v2 import \
    AccountPaymentInstrumentV2
from phonepe.sdk.pg.common.models.response.payment_instruments.payment_instrument_v2_type import \
    PaymentInstrumentV2Type
from phonepe.sdk.pg.common.models.response.rails.payment_rail_type import PaymentRailType
from phonepe.sdk.pg.common.models.response.rails.upi_payment_rail import UpiPaymentRail
from tests.base_custom_checkout_client_for_test import BaseCustomCheckoutClientForTest


class TestCustomCheckoutClient(TestCase):

    def set_first_token_mock(self):
        cur_time = int(time())  # Example value for cur_time
        two_sec_more_cur = int(cur_time + 10)
        token_response_data = f"""{{
            "access_token": "new_token_generated_from_backend",
            "encrypted_access_token": "encrypted_access_token",
            "refresh_token": "refresh_token",
            "expires_in": 200,
            "issued_at": {cur_time},
            "expires_at": {two_sec_more_cur},
            "session_expires_at": 1709630316,
            "token_type": "O-Bearer"
        }}
        """
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

    def set_second_token_mock(self):
        cur_time = int(time())  # Example value for cur_time
        two_sec_more_cur = int(cur_time + 10)
        token_response_data = f"""{{
                    "access_token": "token_invalidated_from_backend",
                    "encrypted_access_token": "encrypted_access_token",
                    "refresh_token": "refresh_token",
                    "expires_in": 200,
                    "issued_at": {cur_time},
                    "expires_at": {two_sec_more_cur},
                    "session_expires_at": 1709630316,
                    "token_type": "O-Bearer"
                }}
                """
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_response_data))

    @responses.activate
    @patch("phonepe.sdk.pg.common.events.constants.SEND_EVENTS_INTERVAL", 10)
    def test_check_status_success(self):

        merchant_transaction_id = "merchant_transaction_id"

        # prepare expected request
        check_status_url = get_pg_base_url(Env.SANDBOX) + ORDER_STATUS_API.format(
            merchant_order_id=merchant_transaction_id)
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
        self.set_first_token_mock()
        BaseCustomCheckoutClientForTest.set_client()
        standard_checkout_client = BaseCustomCheckoutClientForTest.custom_checkout_client

        responses.add(responses.GET, check_status_url, status=200, body="", json=json.loads(response_string),
                      match=[
                          matchers.header_matcher(
                              {'x-source': 'API', 'x-source-version': 'V2', 'x-source-platform': 'BACKEND_PYTHON_SDK',
                               'x-source-platform-version': phonepe.__version__,
                               'Authorization': 'O-Bearer new_token_generated_from_backend',
                               'Content-Type': 'application/json', 'Accept': 'application/json'}
                          )
                      ])
        responses.add(responses.GET, check_status_url, status=401, body="", json=json.loads("""{
                            "success": false,
                            "code": "AUTHORIZATION_FAILED",
                            "message": "Authorization failed [message = Please check the authorization token and try again]",
                            "data": {}
                        }"""),
                      match=[
                          matchers.header_matcher(
                              {'x-source': 'API', 'x-source-version': 'V2', 'x-source-platform': 'BACKEND_PYTHON_SDK',
                               'x-source-platform-version': phonepe.__version__,
                               'Authorization': 'O-Bearer access_token',
                               'Content-Type': 'application/json', 'Accept': 'application/json'}
                          )
                      ])
        self.set_second_token_mock()

        self.assertRaises(UnauthorizedAccess,
                          standard_checkout_client.get_order_status, merchant_transaction_id)

        response_object = BaseCustomCheckoutClientForTest.custom_checkout_client.get_order_status(
            merchant_order_id=merchant_transaction_id)

        expected_order_status_obj = OrderStatusResponse(merchant_id=None, merchant_order_id=None,
                                                        order_id='merchant-order-id', state='COMPLETED', amount=100,
                                                        expire_at=172800000, detailed_error_code=None,
                                                        error_code=None,
                                                        meta_info=MetaInfo(udf1='udf1', udf2='udf2', udf3='udf3',
                                                                           udf4=None, udf5=None),
                                                        payment_details=[PaymentDetail(transaction_id='tid',
                                                                                       payment_mode=PgV2InstrumentType.UPI_QR,
                                                                                       timestamp=22,
                                                                                       amount=22,
                                                                                       state="COMPLETED",
                                                                                       error_code=None,
                                                                                       detailed_error_code=None,
                                                                                       instrument=AccountPaymentInstrumentV2(
                                                                                           type=PaymentInstrumentV2Type.ACCOUNT,
                                                                                           masked_account_number='<maskedAccountNumber>',
                                                                                           ifsc='<ifsc>',
                                                                                           account_holder_name="<accountHolderName>",
                                                                                           account_type="SAVINGS"),
                                                                                       rail=UpiPaymentRail(utr='<utr>',
                                                                                                           type=PaymentRailType.UPI,
                                                                                                           upi_transaction_id='<upiTransactionId>',
                                                                                                           vpa='<vpa>'),
                                                                                       split_instruments=None)])
        assert len(responses.calls) == 3
        assert response_object == expected_order_status_obj
