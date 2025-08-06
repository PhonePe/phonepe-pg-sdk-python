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

from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient


class BaseStandardCheckoutClientForTest(TestCase):
    standard_checkout_client = None

    def setUp(self) -> None:
        BaseStandardCheckoutClientForTest.standard_checkout_client = StandardCheckoutClient.get_instance(
            client_id="client_id",
            client_version=1,
            client_secret="client_secret",
            env=Env.SANDBOX,
            should_publish_events=False)

    @staticmethod
    def get_standard_checkout_client():
        if BaseStandardCheckoutClientForTest.standard_checkout_client is None:
            BaseStandardCheckoutClientForTest.standard_checkout_client = StandardCheckoutClient.get_instance(
                client_id="client_id",
                client_version=1,
                client_secret="client_secret",
                env=Env.SANDBOX,
                should_publish_events=False)
            return BaseStandardCheckoutClientForTest.standard_checkout_client
        return BaseStandardCheckoutClientForTest.standard_checkout_client
