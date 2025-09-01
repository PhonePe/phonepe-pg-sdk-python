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

from phonepe.sdk.pg.common.exceptions import PhonePeException, BadRequest
from phonepe.sdk.pg.env import Env, get_pg_base_url
from phonepe.sdk.pg.payments.v2.models.request.create_sdk_order_request import CreateSdkOrderRequest
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import CREATE_ORDER_API
from tests.base_test_with_oauth import BaseTestWithOauth


class TestException(BaseTestWithOauth):

    @responses.activate
    def test_empty_json(self):
        response_string = """{"orderId": "OMO2403071437388196434033", "state": "PENDING", "expireAt": 1709802878811, "token": "token"}"""

        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        checkout_order_request = CreateSdkOrderRequest.build_standard_checkout_request(
            merchant_order_id="merchant_order_id",
            amount=100,
            redirect_url="url.com")
        responses.add(responses.POST, get_pg_base_url(Env.SANDBOX) + CREATE_ORDER_API, status=503,
                      json=None)

        with self.assertRaises(PhonePeException) as error:
            standard_checkout_client.create_sdk_order(checkout_order_request)

        assert error.exception.http_status_code == 503
        assert error.exception.message == "Service Unavailable"

    @responses.activate
    def test_R9999(self):
        response_string = """{"orderId": "OMO2403071437388196434033", "state": "PENDING", "expireAt": 1709802878811, "token": "token"}"""

        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        checkout_order_request = CreateSdkOrderRequest.build_standard_checkout_request(
            merchant_order_id="merchant_order_id",
            amount=100,
            redirect_url="url.com")
        responses.add(responses.POST, get_pg_base_url(Env.SANDBOX) + CREATE_ORDER_API, status=503,
                      json="R999")

        with self.assertRaises(PhonePeException) as error:
            standard_checkout_client.create_sdk_order(checkout_order_request)

        assert error.exception.http_status_code == 503
        assert error.exception.message == "Service Unavailable"

    @responses.activate
    def test_bad_request(self):
        response_string = """{"orderId": "OMO2403071437388196434033", "state": "PENDING", "expireAt": 1709802878811, "token": "token"}"""

        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        checkout_order_request = CreateSdkOrderRequest.build_standard_checkout_request(
            merchant_order_id="merchant_order_id",
            amount=100,
            redirect_url="url.com")
        responses.add(responses.POST, get_pg_base_url(Env.SANDBOX) + CREATE_ORDER_API, status=400,
                      json=json.dumps("""{
                                "code": "INVALID_CLIENT",
                                "errorCode": "OIM000",
                                "message": "Bad Request: Invalid Client, trackingId: 2123d",
                                "context": {
                                    "error_description": "Client authentication failure"
                                }
                            }"""))

        with self.assertRaises(BadRequest) as error:
            standard_checkout_client.create_sdk_order(checkout_order_request)

        assert error.exception.http_status_code == 400
        assert error.exception.message == "Bad Request"
