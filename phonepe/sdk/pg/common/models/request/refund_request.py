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

from dataclasses_json import dataclass_json, LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class RefundRequest:
    merchant_refund_id: str = field(default=None)
    amount: int = field(default=None)
    original_merchant_order_id: str = field(default=None)

    @staticmethod
    def build_refund_request(merchant_refund_id: str, amount: int, original_merchant_order_id: str):
        return RefundRequest(merchant_refund_id=merchant_refund_id,
                             amount=amount,
                             original_merchant_order_id=original_merchant_order_id)
