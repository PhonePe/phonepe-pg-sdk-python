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

from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import dataclass_json, LetterCase

import phonepe
from phonepe.sdk.pg.common.constants.headers import SDK_TYPE
from phonepe.sdk.pg.common.events.models.enums.event_state import EventState
from phonepe.sdk.pg.common.events.models.enums.flow_type import FlowType
from phonepe.sdk.pg.common.models.request.device_context import DeviceContext
from phonepe.sdk.pg.common.models.payment_flow_type import PaymentFlowType
from phonepe.sdk.pg.subscription.v2.models.request.amount_type import AmountType
from phonepe.sdk.pg.subscription.v2.models.request.auth_workflow_type import AuthWorkflowType
from phonepe.sdk.pg.subscription.v2.models.request.frequency import Frequency
from phonepe.sdk.pg.subscription.v2.models.request.redemption_retry_strategy import RedemptionRetryStrategy


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class EventData:
    # Product type detail (PG, PG_CHECKOUT)
    flow_type: Optional[FlowType] = field(default=None)
    sdk_type: Optional[str] = field(default=SDK_TYPE)
    sdk_version: Optional[str] = field(default=phonepe.__version__)

    # API details
    api_path: Optional[str] = field(default=None)
    amount: Optional[int] = field(default=None)
    merchant_refund_id: Optional[str] = field(default=None)
    transaction_id: Optional[str] = field(default=None)
    event_state: Optional[EventState] = field(default=None)
    payment_instrument: Optional[str] = field(default=None)
    original_merchant_order_id: Optional[str] = field(default=None)
    expire_after: Optional[int] = field(default=None)
    target_app: Optional[str] = field(default=None)
    device_context: Optional[DeviceContext] = field(default=None)

    # Token details
    cached_token_issued_at: Optional[int] = field(default=None)
    cached_token_expires_at: Optional[int] = field(default=None)
    token_fetch_attempt_timestamp: Optional[int] = field(default=None)

    # Subscription Details
    merchant_subscription_id: Optional[str] = field(default=None)
    subscription_expire_at: Optional[int] = field(default=None)
    order_expire_at: Optional[int] = field(default=None)

    # Exception data
    exception_class: Optional[str] = field(default=None)
    exception_message: Optional[str] = field(default=None)
    exception_code: Optional[str] = field(default=None)
    exception_http_status_code: Optional[str] = field(default=None)
    exception_data: Optional[str] = field(default=None)

    inbuilt_exception_repr: Optional[str] = field(default=None)
