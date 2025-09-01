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

from phonepe.sdk.pg.common.models.response.payment_flow_response_mapper import map_to_payment_flow_response
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.payments.v2.models.response.payment_detail import PaymentDetail
from phonepe.sdk.pg.common.models.response.payment_flow_response import PaymentFlowResponse


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class OrderStatusResponse:
    merchant_id: Optional[str] = field(default=None)
    merchant_order_id: Optional[str] = field(default=None)
    order_id: Optional[str] = field(default=None)
    state: Optional[str] = field(default=None)
    amount: Optional[int] = field(default=None)
    payable_amount: Optional[int] = field(default=None)
    fee_amount: Optional[int] = field(default=None)
    expire_at: Optional[int] = field(default=None)
    detailed_error_code: Optional[str] = field(default=None)
    error_code: Optional[str] = field(default=None)
    meta_info: Optional[MetaInfo] = field(default=None)
    payment_details: Optional[List[PaymentDetail]] = field(default=None)
    payment_flow: Optional[PaymentFlowResponse] = field(default=None)

    def __post_init__(self):
        self.payment_flow = map_to_payment_flow_response(self.payment_flow)
