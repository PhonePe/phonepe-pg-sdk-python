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

from typing import Union

from phonepe.sdk.pg.common.models.payment_flow_type import PaymentFlowType
from phonepe.sdk.pg.common.models.response.payment_flow_response import (
    PaymentFlowResponse,
)
from phonepe.sdk.pg.subscription.v2.models.response.subscription_redemption_payment_flow_response import (
    SubscriptionRedemptionPaymentFlowResponse,
)
from phonepe.sdk.pg.subscription.v2.models.response.subscription_setup_payment_flow_response import (
    SubscriptionSetupPaymentFlowResponse,
)

PAYMENT_FLOW_MAPPER = {
    PaymentFlowType.SUBSCRIPTION_SETUP: SubscriptionSetupPaymentFlowResponse,
    PaymentFlowType.SUBSCRIPTION_REDEMPTION: SubscriptionRedemptionPaymentFlowResponse,
}


def map_to_payment_flow_response(
        payment_flow_object: Union[dict, PaymentFlowResponse]
) -> Union[dict, PaymentFlowResponse]:
    if (
            payment_flow_object
            and isinstance(payment_flow_object, dict)
            and "type" in payment_flow_object
            and payment_flow_object["type"] in PAYMENT_FLOW_MAPPER
    ):
        payment_flow_type = PAYMENT_FLOW_MAPPER.get(payment_flow_object.get("type"))
        return payment_flow_type.from_dict(payment_flow_object)
    return payment_flow_object
