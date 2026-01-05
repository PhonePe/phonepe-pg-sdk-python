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
from phonepe.sdk.pg.payments.v2.custom_checkout.custom_checkout_constants import CREATE_ORDER_API as custom_order_api
from phonepe.sdk.pg.payments.v2.models.request.create_sdk_order_request import CreateSdkOrderRequest
from phonepe.sdk.pg.payments.v2.models.response.create_sdk_order_response import \
    CreateSdkOrderResponse
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import CREATE_ORDER_API
from tests.base_test_with_oauth import BaseTestWithOauth


class TestCreateOrderWithOauth(BaseTestWithOauth):

    @responses.activate
    def test_create_order_success(self):
        response_string = """{"orderId": "OMO2403071437388196434033", "state": "PENDING", "expireAt": 1709802878811, "token": "token"}"""

        standard_checkout_client = BaseTestWithOauth.standard_checkout_client

        checkout_order_request = CreateSdkOrderRequest.build_standard_checkout_request(
            merchant_order_id="merchant_order_id",
            amount=100,
            redirect_url="url.com")
        responses.add(responses.POST, get_pg_base_url(Env.SANDBOX) + CREATE_ORDER_API, status=200,
                      json=json.loads(response_string))

        actual_response = standard_checkout_client.create_sdk_order(sdk_order_request=checkout_order_request)
        expected_response = CreateSdkOrderResponse(order_id='OMO2403071437388196434033',
                                                   state='PENDING',
                                                   expire_at=1709802878811,
                                                   token='token')

        assert expected_response == actual_response

    @responses.activate
    def test_create_order_success_custom(self):
        response_string = """{"orderId": "OMO2403071437388196434033", "state": "PENDING", "expireAt": 1709802878811, "token": "token"}"""

        standard_checkout_client = BaseTestWithOauth.custom_checkout_client

        checkout_order_request = CreateSdkOrderRequest.build_custom_checkout_request(
            merchant_order_id="merchant_order_id",
            amount=100)
        responses.add(responses.POST, get_pg_base_url(Env.SANDBOX) + custom_order_api, status=200,
                      json=json.loads(response_string))

        actual_response = standard_checkout_client.create_sdk_order(sdk_order_request=checkout_order_request)
        expected_response = CreateSdkOrderResponse(order_id='OMO2403071437388196434033',
                                                   state='PENDING',
                                                   expire_at=1709802878811,
                                                   token='token')

        assert expected_response == actual_response

    @responses.activate
    def test_create_order_success_custom_disable_retry_true(self):
        response_string = """{"orderId": "OMO2403071437388196434033", "state": "PENDING", "expireAt": 1709802878811, "token": "token"}"""
        standard_checkout_client = BaseTestWithOauth.custom_checkout_client
        checkout_order_request = CreateSdkOrderRequest.build_custom_checkout_request(
            merchant_order_id="merchant_order_id",
            amount=100,
            disable_payment_retry=True)
        assert checkout_order_request.disable_payment_retry

        responses.add(responses.POST, get_pg_base_url(Env.SANDBOX) + custom_order_api, status=200,
                      json=json.loads(response_string))

        actual_response = standard_checkout_client.create_sdk_order(sdk_order_request=checkout_order_request)
        expected_response = CreateSdkOrderResponse(order_id='OMO2403071437388196434033',
                                                   state='PENDING',
                                                   expire_at=1709802878811,
                                                   token='token')

        assert expected_response == actual_response

    @responses.activate
    def test_create_order_success_custom_disable_retry_false(self):
        response_string = """{"orderId": "OMO2403071437388196434033", "state": "PENDING", "expireAt": 1709802878811, "token": "token"}"""
        standard_checkout_client = BaseTestWithOauth.custom_checkout_client
        checkout_order_request = CreateSdkOrderRequest.build_custom_checkout_request(
            merchant_order_id="merchant_order_id",
            amount=100,
            disable_payment_retry=False)
        assert not checkout_order_request.disable_payment_retry

        responses.add(responses.POST, get_pg_base_url(Env.SANDBOX) + custom_order_api, status=200,
                      json=json.loads(response_string))

        actual_response = standard_checkout_client.create_sdk_order(sdk_order_request=checkout_order_request)
        expected_response = CreateSdkOrderResponse(order_id='OMO2403071437388196434033',
                                                   state='PENDING',
                                                   expire_at=1709802878811,
                                                   token='token')

        assert expected_response == actual_response

