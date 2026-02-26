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
from phonepe.sdk.pg.payments.v2.models.request.prefill_user_login_details import (
    PrefillUserLoginDetails,
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


PAY_RESPONSE = {
    "orderId": "OMO2403071446458436434329",
    "state": "PENDING",
    "expireAt": 1709803425841,
    "redirectUrl": "https://pay.phonepe.com/redirect",
}

EXPECTED_PAY_RESPONSE = StandardCheckoutPayResponse(
    order_id="OMO2403071446458436434329",
    state="PENDING",
    expire_at=1709803425841,
    redirect_url="https://pay.phonepe.com/redirect",
)


class TestPrefillUserLoginDetails(BaseTestWithOauth):

    # ------------------------------------------------------------------ #
    # Model-level tests                                                    #
    # ------------------------------------------------------------------ #

    def test_prefill_user_login_details_with_phone_number(self):
        """PrefillUserLoginDetails stores phone_number correctly."""
        prefill = PrefillUserLoginDetails(phone_number="9999999999")
        assert prefill.phone_number == "9999999999"

    def test_prefill_user_login_details_default_is_none(self):
        """PrefillUserLoginDetails defaults phone_number to None."""
        prefill = PrefillUserLoginDetails()
        assert prefill.phone_number is None

    def test_prefill_serializes_to_camel_case(self):
        """PrefillUserLoginDetails serialises to camelCase JSON."""
        prefill = PrefillUserLoginDetails(phone_number="9999999999")
        data = json.loads(prefill.to_json())
        assert "phoneNumber" in data
        assert data["phoneNumber"] == "9999999999"
        assert "phone_number" not in data

    # ------------------------------------------------------------------ #
    # StandardCheckoutPayRequest integration tests                        #
    # ------------------------------------------------------------------ #

    def test_build_request_with_prefill_user_login_details(self):
        """build_request() correctly wires prefill_user_login_details."""
        prefill = PrefillUserLoginDetails(phone_number="9999999999")
        request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="ORDER001",
            amount=1000,
            redirect_url="https://merchant.com/redirect",
            prefill_user_login_details=prefill,
        )
        assert request.prefill_user_login_details is not None
        assert request.prefill_user_login_details.phone_number == "9999999999"

    def test_build_request_without_prefill_user_login_details(self):
        """build_request() leaves prefill_user_login_details as None when not provided."""
        request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="ORDER002",
            amount=1000,
            redirect_url="https://merchant.com/redirect",
        )
        assert request.prefill_user_login_details is None

    def test_prefill_user_login_details_in_serialized_payload(self):
        """prefillUserLoginDetails appears in the camelCase JSON payload."""
        prefill = PrefillUserLoginDetails(phone_number="9999999999")
        request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="ORDER003",
            amount=1000,
            redirect_url="https://merchant.com/redirect",
            prefill_user_login_details=prefill,
        )
        payload = json.loads(request.to_json())
        assert "prefillUserLoginDetails" in payload
        assert payload["prefillUserLoginDetails"]["phoneNumber"] == "9999999999"

    def test_no_prefill_field_absent_from_serialized_payload(self):
        """prefillUserLoginDetails is absent from the JSON payload when not set."""
        request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="ORDER004",
            amount=1000,
            redirect_url="https://merchant.com/redirect",
        )
        payload = json.loads(request.to_json())
        # The field should either be absent or None — it must not carry a value.
        assert payload.get("prefillUserLoginDetails") is None

    # ------------------------------------------------------------------ #
    # End-to-end HTTP tests (pay API)                                     #
    # ------------------------------------------------------------------ #

    @responses.activate
    def test_pay_with_prefill_user_login_details(self):
        """pay() succeeds when prefill_user_login_details is provided."""
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        prefill = PrefillUserLoginDetails(phone_number="9999999999")
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="ORDER005",
            amount=1000,
            redirect_url="https://merchant.com/redirect",
            prefill_user_login_details=prefill,
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + PAY_API,
            status=200,
            json=PAY_RESPONSE,
        )

        actual_response = standard_checkout_client.pay(pay_request=pay_request)
        assert actual_response == EXPECTED_PAY_RESPONSE

    @responses.activate
    def test_pay_with_prefill_sends_phone_number_in_body(self):
        """pay() sends prefillUserLoginDetails.phoneNumber in the request body."""
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        prefill = PrefillUserLoginDetails(phone_number="9999999999")
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="ORDER006",
            amount=500,
            redirect_url="https://merchant.com/redirect",
            prefill_user_login_details=prefill,
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + PAY_API,
            status=200,
            json=PAY_RESPONSE,
        )

        standard_checkout_client.pay(pay_request=pay_request)

        sent_body = json.loads(responses.calls[-1].request.body)
        assert "prefillUserLoginDetails" in sent_body
        assert sent_body["prefillUserLoginDetails"]["phoneNumber"] == "9999999999"

    @responses.activate
    def test_pay_without_prefill_omits_field_from_body(self):
        """pay() does not send prefillUserLoginDetails when it is not set."""
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="ORDER007",
            amount=500,
            redirect_url="https://merchant.com/redirect",
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + PAY_API,
            status=200,
            json=PAY_RESPONSE,
        )

        standard_checkout_client.pay(pay_request=pay_request)

        sent_body = json.loads(responses.calls[-1].request.body)
        assert sent_body.get("prefillUserLoginDetails") is None

    @responses.activate
    def test_pay_with_prefill_and_disable_payment_retry(self):
        """pay() works correctly when both prefill and disable_payment_retry are set."""
        standard_checkout_client = BaseTestWithOauth.standard_checkout_client
        prefill = PrefillUserLoginDetails(phone_number="8888888888")
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id="ORDER008",
            amount=2000,
            redirect_url="https://merchant.com/redirect",
            disable_payment_retry=True,
            prefill_user_login_details=prefill,
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + PAY_API,
            status=200,
            json=PAY_RESPONSE,
        )

        actual_response = standard_checkout_client.pay(pay_request=pay_request)

        assert actual_response == EXPECTED_PAY_RESPONSE
        assert pay_request.disable_payment_retry is True
        assert pay_request.prefill_user_login_details.phone_number == "8888888888"

        sent_body = json.loads(responses.calls[-1].request.body)
        assert sent_body.get("disablePaymentRetry") is True
        assert sent_body["prefillUserLoginDetails"]["phoneNumber"] == "8888888888"
