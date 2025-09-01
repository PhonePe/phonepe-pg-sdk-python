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

from typing import Optional
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json, LetterCase

from phonepe.sdk.pg.subscription.v2.models.request.amount_type import AmountType
from phonepe.sdk.pg.subscription.v2.models.request.auth_workflow_type import AuthWorkflowType
from phonepe.sdk.pg.subscription.v2.models.request.frequency import Frequency


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SubscriptionStatusResponseV2:
    merchant_subscription_id: Optional[str] = field(default=None)
    subscription_id : Optional[str] = field(default=None)
    state: Optional[str] = field(default=None)
    auth_workflow_type : Optional[AuthWorkflowType] = field(default=None)
    amount_type: Optional[AmountType] = field(default=None)
    max_amount: Optional[int] = field(default=None)
    frequency: Optional[Frequency] = field(default=None)
    expire_at: Optional[int] = field(default=None)
    pause_start_date: Optional[int] = field(default=None)
    pause_end_date: Optional[int] = field(default=None)
