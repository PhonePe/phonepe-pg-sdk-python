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
from time import time
from unittest.mock import patch

import responses

from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.env import Env, get_pg_base_url, get_oauth_base_url
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.payments.v2.models.request.pg_v2_instrument_type import PgV2InstrumentType
from phonepe.sdk.pg.common.models.response.order_status_response import OrderStatusResponse
from phonepe.sdk.pg.payments.v2.models.response.payment_detail import PaymentDetail
from phonepe.sdk.pg.common.models.response.payment_instruments.account_payment_instrument_v2 import \
    AccountPaymentInstrumentV2
from phonepe.sdk.pg.common.models.response.payment_instruments.payment_instrument_v2_type import \
    PaymentInstrumentV2Type
from phonepe.sdk.pg.common.models.response.rails.payment_rail_type import PaymentRailType
from phonepe.sdk.pg.common.models.response.rails.upi_payment_rail import UpiPaymentRail
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import ORDER_STATUS_API
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from tests.base_standard_checkout_client_for_test import BaseStandardCheckoutClientForTest


from tests.base_custom_checkout_client_for_test import BaseCustomCheckoutClientForTest
from phonepe.sdk.pg.payments.v2.custom_checkout_client import CustomCheckoutClient


from phonepe.sdk.pg.subscription.v2.subscription_client import SubscriptionClient
from tests.base_subscription_client_for_test import BaseSubscriptionClientForTest

# Far-future issued_at/expires_at (mirrors the pattern used by BaseTestWithOauth and the other
# Base*ClientForTest fixtures) so any client constructed against this fixture never reaches its
# proactive-refresh half-life during a real test run, and thus never leaks a background HTTP call
# into a later, unrelated test's active responses mock.
_LONG_LIVED_TOKEN_RESPONSE = {
    "access_token": "access_token",
    "encrypted_access_token": "encrypted_access_token",
    "refresh_token": "refresh_token",
    "expires_in": 5014,
    "issued_at": 2014804440,
    "expires_at": 2014804440,
    "session_expires_at": 2014804440,
    "token_type": "O-Bearer",
}


def _add_long_lived_oauth_mock():
    responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                  json=_LONG_LIVED_TOKEN_RESPONSE)


class TestSingletonObject(BaseStandardCheckoutClientForTest, BaseCustomCheckoutClientForTest,
                          BaseSubscriptionClientForTest):

    def test_singleton_via_get_instance(self):
        standard_checkout_client = StandardCheckoutClient.get_instance(client_id="client_id",
                                                                       client_version=1,
                                                                       client_secret="client_secret",
                                                                       env=Env.SANDBOX,
                                                                       should_publish_events=False)
        assert standard_checkout_client == BaseStandardCheckoutClientForTest.standard_checkout_client

    @responses.activate
    def test_singleton_with_diff_params(self):
        # client_id_02/client_id_03 may already be cached (e.g. by tests/test_token_service.py's
        # test_static, which uses the same ids) - this mock is a no-op then, harmless since
        # @responses.activate defaults to assert_all_requests_are_fired=False.
        _add_long_lived_oauth_mock()
        instance = StandardCheckoutClient.get_instance(
            client_id="client_id_02",
            client_secret="client_secret",
            client_version=1,
            env=Env.SANDBOX
        )
        # This will return the same already initiated instance
        assert instance is StandardCheckoutClient.get_instance("client_id_02", "client_secret", 1, Env.SANDBOX)
        self.assertTrue(
            instance is StandardCheckoutClient.get_instance("client_id_02", "client_secret", 1, Env.SANDBOX))

        instance2 = StandardCheckoutClient.get_instance(
            client_id="client_id_03",
            client_secret="client_secret3",
            client_version=1,
            env=Env.SANDBOX
        )
        assert instance2 is StandardCheckoutClient.get_instance("client_id_03", "client_secret3", 1, Env.SANDBOX)
        self.assertTrue(
            instance is not instance2)

    @responses.activate
    def test_custom_checkout_singleton_via_get_instance(self):
        # CustomCheckoutClient's own setUp() doesn't run for this multiply-inherited test class
        # (MRO only calls the first parent's setUp(), i.e. BaseStandardCheckoutClientForTest's),
        # so this singleton may not exist yet if this test runs in isolation - this mock covers
        # that case; it's a harmless no-op if the singleton is already cached from elsewhere.
        _add_long_lived_oauth_mock()
        custom_checkout_client = CustomCheckoutClient.get_instance(client_id="client_id",
                                                                   client_version=1,
                                                                   client_secret="client_secret",
                                                                   env=Env.SANDBOX,
                                                                   should_publish_events=False)
        assert custom_checkout_client == BaseCustomCheckoutClientForTest.custom_checkout_client

    @responses.activate
    def test_custom_checkout_singleton_with_diff_params(self):
        _add_long_lived_oauth_mock()
        instance = CustomCheckoutClient.get_instance(
            client_id="client_id_02",
            client_secret="client_secret",
            client_version=1,
            env=Env.SANDBOX
        )
        # This will return the same already initiated instance
        assert instance is CustomCheckoutClient.get_instance("client_id_02", "client_secret", 1, Env.SANDBOX)
        self.assertTrue(instance is CustomCheckoutClient.get_instance("client_id_02", "client_secret", 1, Env.SANDBOX))

        new_instance = CustomCheckoutClient.get_instance(
            client_id="client_id_03",
            client_secret="client_secret",
            client_version=1,
            env=Env.SANDBOX
        )
        self.assertTrue(
            new_instance is not CustomCheckoutClient.get_instance("client_id_02", "client_secret", 1, Env.SANDBOX))

    def test_subscription_singleton_via_get_instance(self):
        subscription_client = SubscriptionClient.get_instance(client_id="client_id",
                                                              client_version=1,
                                                              client_secret="client_secret",
                                                              env=Env.SANDBOX,
                                                              should_publish_events=False)
        assert subscription_client == BaseSubscriptionClientForTest.subscription_client

    @responses.activate
    def test_subscription_singleton_with_diff_params(self):
        _add_long_lived_oauth_mock()
        instance = SubscriptionClient.get_instance(
            client_id="client_id_02",
            client_secret="client_secret",
            client_version=1,
            env=Env.SANDBOX
        )
        # This will return the same already initiated instance
        assert instance is SubscriptionClient.get_instance("client_id_02", "client_secret", 1, Env.SANDBOX)
        self.assertTrue(instance is SubscriptionClient.get_instance("client_id_02", "client_secret", 1, Env.SANDBOX))

        new_instance = SubscriptionClient.get_instance(
            client_id="client_id_03",
            client_secret="client_secret",
            client_version=1,
            env=Env.SANDBOX
        )
        self.assertTrue(
            new_instance is not SubscriptionClient.get_instance("client_id_02", "client_secret", 1, Env.SANDBOX))

    def set_first_token_mock(self, cur_time):
        two_sec_more_cur = int(cur_time + 4)
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
    def test_multiple_client_expired_multiple_oauth_call(self):

        merchant_transaction_id = "merchant_transaction_id"
        cur_time = int(time())

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
        # Each construction below now eagerly fetches its own token immediately (5 eager
        # fetches), on top of whatever additional refetches happen later from the patched-clock
        # get_order_status() calls - set_first_token_mock's single registered mock is reused
        # (responses persists a registered mock for every matching request) for all of them.
        self.set_first_token_mock(cur_time)
        standard_checkout_client0 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client0.close)
        standard_checkout_client1 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client1.close)
        standard_checkout_client2 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client2.close)
        standard_checkout_client3 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client3.close)
        standard_checkout_client4 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client4.close)

        responses.add(responses.GET, check_status_url, status=200, body="", json=json.loads(response_string))
        with patch.object(standard_checkout_client0._token_service, 'get_current_time',
                          return_value=int(cur_time + 10)):
            response_object = standard_checkout_client0.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client1._token_service, 'get_current_time',
                          return_value=int(cur_time + 10)):
            response_object = standard_checkout_client1.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client2._token_service, 'get_current_time',
                          return_value=int(cur_time + 10)):
            response_object = standard_checkout_client2.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client3._token_service, 'get_current_time',
                          return_value=int(cur_time + 10)):
            response_object = standard_checkout_client3.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client4._token_service, 'get_current_time',
                          return_value=int(cur_time + 10)):
            response_object = standard_checkout_client4.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client0._token_service, 'get_current_time',
                          return_value=int(cur_time + 10)):
            response_object = standard_checkout_client0.get_order_status(merchant_order_id=merchant_transaction_id)

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
        # 5 eager fetches (1 per construction) + 6 lazy refetches (each get_order_status() call
        # sees an immediately-expired token under the patched cur_time+10 clock, since the mocked
        # token's half-life is always cur_time+2) + 6 order-status GETs = 17.
        assert len(responses.calls) == 17
        assert response_object == expected_order_status_obj

    @responses.activate
    def test_multiple_client_multiple_oauth_call(self):
        merchant_transaction_id = "merchant_transaction_id"
        cur_time = int(time())

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
        self.set_first_token_mock(cur_time)
        standard_checkout_client0 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client0.close)
        standard_checkout_client1 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client1.close)
        standard_checkout_client2 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client2.close)
        standard_checkout_client3 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client3.close)
        standard_checkout_client4 = StandardCheckoutClient(client_id="client_id",
                                                           client_version=1,
                                                           client_secret="client_secret",
                                                           env=Env.SANDBOX)
        self.addCleanup(standard_checkout_client4.close)

        responses.add(responses.GET, check_status_url, status=200, body="", json=json.loads(response_string))
        with patch.object(standard_checkout_client0._token_service, 'get_current_time',
                          return_value=int(cur_time + 1)):
            response_object = standard_checkout_client0.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client1._token_service, 'get_current_time',
                          return_value=int(cur_time + 1)):
            response_object = standard_checkout_client1.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client2._token_service, 'get_current_time',
                          return_value=int(cur_time + 1)):
            response_object = standard_checkout_client2.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client3._token_service, 'get_current_time',
                          return_value=int(cur_time + 1)):
            response_object = standard_checkout_client3.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client4._token_service, 'get_current_time',
                          return_value=int(cur_time + 1)):
            response_object = standard_checkout_client4.get_order_status(merchant_order_id=merchant_transaction_id)
        with patch.object(standard_checkout_client0._token_service, 'get_current_time',
                          return_value=int(cur_time + 1)):
            response_object = standard_checkout_client0.get_order_status(merchant_order_id=merchant_transaction_id)

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
        # 5 eager fetches (1 per construction) suffice here: half-life (cur_time+2) is still in
        # the future under the patched cur_time+1 clock, so none of the 6 get_order_status()
        # calls need to refetch - only reuse each instance's own already-cached token.
        assert len(responses.calls) == 11  # 5 oauth (eager) + 6 order status
        assert response_object == expected_order_status_obj
