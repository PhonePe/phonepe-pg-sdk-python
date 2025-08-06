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

import time
from dataclasses import asdict
import responses

from phonepe.sdk.pg.common.exceptions import BadRequest, PhonePeException
from phonepe.sdk.pg.common.http_client_modules.phonepe_response import PhonePeResponse
from phonepe.sdk.pg.common.models.request.pg_payment_request import PgPaymentRequest
from phonepe.sdk.pg.common.models.response.pg_payment_response import PgPaymentResponse
from phonepe.sdk.pg.env import Env, get_pg_base_url
from phonepe.sdk.pg.subscription.v2.models.request.amount_type import AmountType
from phonepe.sdk.pg.subscription.v2.models.request.auth_workflow_type import (
    AuthWorkflowType,
)
from phonepe.sdk.pg.subscription.v2.models.subscription_constants import SETUP_API
from phonepe.sdk.pg.subscription.v2.models.request.frequency import Frequency
from http import HTTPStatus
from tests.base_test_with_oauth import BaseTestWithOauth


class SubscriptionSetup(BaseTestWithOauth):

    @responses.activate
    def test_setup_via_upi_collect_success(self):
        merchant_order_id = "merchantOrderId"
        amount = 100
        vpa = "vpa"
        auth_workflow_type = AuthWorkflowType.TRANSACTION
        amount_type = AmountType.FIXED
        frequency = Frequency.ON_DEMAND
        max_amount = 100

        response_str = """{
                            "orderId" : "OMO12344",
                            "state" : "PENDING"
                        }"""

        setup_request = PgPaymentRequest.build_subscription_setup_upi_collect(
            merchant_order_id=merchant_order_id,
            merchant_subscription_id=merchant_order_id,
            amount=amount,
            max_amount=max_amount,
            vpa=vpa,
            message="",
            auth_workflow_type=auth_workflow_type,
            amount_type=amount_type,
            frequency=frequency,
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + SETUP_API,
            body=response_str,
            status=HTTPStatus.OK,
        )

        actual_response = BaseTestWithOauth.subscription_client.setup(
            request=setup_request
        )
        expected_response = PgPaymentResponse(order_id="OMO12344", state="PENDING")
        assert actual_response == expected_response

    @responses.activate
    def test_setup_via_upi_intent_success(self):
        merchant_order_id = "merchantOrderId"
        response_str = """{
                            "orderId" : "OMO12344",
                            "state" : "PENDING",
                            "intentUrl" : "dummy-intent-url"
                        }"""

        setup_request = PgPaymentRequest.build_subscription_setup_upi_intent(
            merchant_order_id=merchant_order_id,
            merchant_subscription_id=merchant_order_id,
            amount=200,
            device_os="IOS",
            merchant_callback_scheme="",
            target_app="PHONEPE",
            auth_workflow_type=AuthWorkflowType.TRANSACTION,
            amount_type=AmountType.FIXED,
            order_expire_at=int(time.time() * 1000) + 1000000,
            subscription_expire_at=int(time.time() * 1000) + 1000000,
            frequency=Frequency.ON_DEMAND,
            max_amount=200,
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + SETUP_API,
            body=response_str,
            status=HTTPStatus.OK,
        )

        actual_response = BaseTestWithOauth.subscription_client.setup(
            request=setup_request
        )
        expected_response = PgPaymentResponse(
            order_id="OMO12344", state="PENDING", intent_url="dummy-intent-url"
        )
        assert actual_response == expected_response

    @responses.activate
    def test_setup_failure_via_collect(self):
        merchant_order_id = "merchantOrderId"
        merchant_subscription_id = "merchantSubscriptionId"

        setup_request = PgPaymentRequest.build_subscription_setup_upi_collect(
            merchant_order_id=merchant_order_id,
            merchant_subscription_id=merchant_subscription_id,
            amount=200,
            vpa="<vpa>",
            message="message",
            auth_workflow_type=AuthWorkflowType.TRANSACTION,
            amount_type=AmountType.FIXED,
            order_expire_at=int(time.time() * 1000) + 1000000,
            subscription_expire_at=int(time.time() * 1000) + 1000000,
            frequency=Frequency.ON_DEMAND,
            max_amount=200,
        )

        phonepe_response = PhonePeResponse(
            code="Bad Request", message="message", data={"a": "b"}
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + SETUP_API,
            json=asdict(phonepe_response),
            status=HTTPStatus.BAD_REQUEST,
        )

        with self.assertRaises(PhonePeException) as cm:
            BaseTestWithOauth.subscription_client.setup(setup_request)

        self.assertEqual(cm.exception.http_status_code, 400)
        self.assertEqual(cm.exception.code, "Bad Request")
        self.assertIsInstance(cm.exception, BadRequest)

    @responses.activate
    def test_setup_failure_via_intent(self):
        setup_request = PgPaymentRequest.build_subscription_setup_upi_intent(
            merchant_order_id="merchantOrderId",
            merchant_subscription_id="merchantSubscriptionId",
            amount=200,
            device_os="IOS",
            merchant_callback_scheme="",
            target_app="PHONEPE",
            auth_workflow_type=AuthWorkflowType.TRANSACTION,
            amount_type=AmountType.FIXED,
            order_expire_at=int(time.time() * 1000) + 1000000,
            subscription_expire_at=int(time.time() * 1000) + 1000000,
            frequency=Frequency.ON_DEMAND,
            max_amount=200,
        )

        phonepe_response = PhonePeResponse(
            code="Bad Request", message="message", data={"a": "b"}
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + SETUP_API,
            json=asdict(phonepe_response),
            status=HTTPStatus.BAD_REQUEST,
        )

        with self.assertRaises(PhonePeException) as cm:
            BaseTestWithOauth.subscription_client.setup(setup_request)

        self.assertEqual(cm.exception.http_status_code, 400)
        self.assertEqual(cm.exception.code, "Bad Request")
        self.assertIsInstance(cm.exception, BadRequest)
