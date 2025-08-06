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

from phonepe.sdk.pg.env import Env, get_pg_base_url
from phonepe.sdk.pg.subscription.v2.models.subscription_constants import (
    CANCEL_SUBSCRIPTION_API,
)
from tests.base_test_with_oauth import BaseTestWithOauth


class TestCancelSubscription(BaseTestWithOauth):
    @responses.activate
    def test_cancel_subscription(self):
        merchant_subscription_id = "merchant_subscription_id"
        url = CANCEL_SUBSCRIPTION_API.format(
            merchant_subscription_id=merchant_subscription_id
        )
        responses.add(
            responses.POST,
            get_pg_base_url(Env.SANDBOX) + url,
            status=HTTPStatus.OK,
            body="",
        )
        actual_response = BaseTestWithOauth.subscription_client.cancel_subscription(
            merchant_subscription_id
        )
        self.assertEqual(actual_response, None)
