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
from typing import Optional, List

from dataclasses_json import dataclass_json, LetterCase

from phonepe.sdk.pg.payments.v2.models.response.payment_refund_detail import PaymentRefundDetail


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class RefundStatusResponse:
    merchant_id: Optional[str] = field(default=None)
    merchant_refund_id: Optional[str] = field(default=None)
    original_merchant_order_id: Optional[str] = field(default=None)
    amount: Optional[int] = field(default=None)
    state: Optional[str] = field(default=None)
    payment_details: Optional[List[PaymentRefundDetail]] = field(default=None)
