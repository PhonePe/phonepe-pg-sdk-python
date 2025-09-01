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

from phonepe.sdk.pg.common.models.response.payment_instruments.payment_instrument_v2 import PaymentInstrumentV2
from phonepe.sdk.pg.common.models.response.payment_instruments.payment_instrument_v2_type import \
    PaymentInstrumentV2Type


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AccountPaymentInstrumentV2(PaymentInstrumentV2):
    type: Optional[PaymentInstrumentV2Type] = field(default=None)
    masked_account_number: Optional[str] = field(default=None)
    ifsc: Optional[str] = field(default=None)
    account_holder_name: Optional[str] = field(default=None)
    account_type: Optional[str] = field(default=None)
