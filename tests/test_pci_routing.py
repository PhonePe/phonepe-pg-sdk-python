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
from unittest import TestCase

import responses

from phonepe.sdk.pg.common.constants.base_urls import PROD_PCI_PG_BASE_URL, SANDBOX_PG_BASE_URL
from phonepe.sdk.pg.common.models.request.pg_payment_request import PgPaymentRequest
from phonepe.sdk.pg.common.models.response.pg_payment_response import PgPaymentResponse
from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.env import Env, get_pg_base_url, get_oauth_base_url, get_pci_pg_base_url
from phonepe.sdk.pg.payments.v2.custom_checkout.custom_checkout_constants import PAY_API
from phonepe.sdk.pg.payments.v2.custom_checkout_client import CustomCheckoutClient
from tests.base_test_with_oauth import BaseTestWithOauth


_PAY_RESPONSE = json.loads(
    '{"orderId": "ORDER123", "state": "PENDING", "expireAt": 9999999999, "redirectUrl": "https://redirect.example.com"}'
)
_EXPECTED_RESPONSE = PgPaymentResponse(
    order_id="ORDER123",
    state="PENDING",
    expire_at=9999999999,
    redirect_url="https://redirect.example.com",
)


class TestPciRouting(BaseTestWithOauth):
    """Tests that CARD and TOKEN instruments are routed to the PCI host URL."""

    @responses.activate
    def test_card_instrument_routes_to_pci_host(self):
        """CARD payment must hit the PCI host (SANDBOX falls back to SANDBOX_PG_BASE_URL)."""
        pci_base_url = get_pci_pg_base_url(Env.SANDBOX)
        responses.add(responses.POST, pci_base_url + PAY_API, status=200, json=_PAY_RESPONSE)

        pay_request = PgPaymentRequest.build_card_pay_request(
            merchant_order_id="CARD_ORDER_01",
            amount=1000,
            auth_mode="NATIVE",
            encryption_key_id=1,
            encrypted_card_number="enc_card",
            encrypted_cvv="enc_cvv",
            expiry_month="12",
            expiry_year="2030",
            card_holder_name="Test User",
            redirect_url="https://redirect.example.com",
        )

        actual = self.custom_checkout_client.pay(pay_request=pay_request)
        self.assertEqual(actual, _EXPECTED_RESPONSE)
        # Verify the request was made to the PCI URL, not the default one
        self.assertEqual(len(responses.calls), 1)
        self.assertIn(pci_base_url, responses.calls[0].request.url)

    @responses.activate
    def test_token_instrument_routes_to_pci_host(self):
        """TOKEN payment must hit the PCI host."""
        pci_base_url = get_pci_pg_base_url(Env.SANDBOX)
        responses.add(responses.POST, pci_base_url + PAY_API, status=200, json=_PAY_RESPONSE)

        pay_request = PgPaymentRequest.build_token_pay_request(
            merchant_order_id="TOKEN_ORDER_01",
            amount=1000,
            auth_mode="NATIVE",
            encryption_key_id=1,
            encrypted_token="enc_token",
            encrypted_cvv="enc_cvv",
            cryptogram="crypto",
            pan_suffix="1234",
            expiry_month="12",
            expiry_year="2030",
            redirect_url="https://redirect.example.com",
        )

        actual = self.custom_checkout_client.pay(pay_request=pay_request)
        self.assertEqual(actual, _EXPECTED_RESPONSE)
        self.assertEqual(len(responses.calls), 1)
        self.assertIn(pci_base_url, responses.calls[0].request.url)

    @responses.activate
    def test_upi_collect_instrument_uses_default_host(self):
        """UPI_COLLECT payment must NOT route to PCI host — uses default pg_host_url."""
        default_base_url = get_pg_base_url(Env.SANDBOX)
        responses.add(responses.POST, default_base_url + PAY_API, status=200, json=_PAY_RESPONSE)

        pay_request = PgPaymentRequest.build_upi_collect_pay_via_vpa_request(
            merchant_order_id="UPI_ORDER_01",
            amount=1000,
            vpa="user@upi",
            message="Pay for order",
        )

        actual = self.custom_checkout_client.pay(pay_request=pay_request)
        self.assertEqual(actual, _EXPECTED_RESPONSE)
        self.assertEqual(len(responses.calls), 1)
        self.assertIn(default_base_url, responses.calls[0].request.url)

    def test_pci_pg_base_url_constant_is_correct(self):
        """PROD_PCI_PG_BASE_URL must point to the cards subdomain."""
        self.assertEqual(PROD_PCI_PG_BASE_URL, "https://cards.phonepe.com/apis/pg")

    def test_pci_pg_base_url_production(self):
        """get_pci_pg_base_url returns cards subdomain for PRODUCTION."""
        self.assertEqual(get_pci_pg_base_url(Env.PRODUCTION), PROD_PCI_PG_BASE_URL)

    def test_pci_pg_base_url_sandbox_fallback(self):
        """get_pci_pg_base_url falls back to SANDBOX_PG_BASE_URL for SANDBOX."""
        self.assertEqual(get_pci_pg_base_url(Env.SANDBOX), SANDBOX_PG_BASE_URL)
