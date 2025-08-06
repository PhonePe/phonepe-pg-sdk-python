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

from phonepe.sdk.pg.common.models.request.instrument_constraint import InstrumentConstraint
from phonepe.sdk.pg.payments.v2.models.request.payment_instrument_type import PaymentInstrumentType


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AccountConstraint(InstrumentConstraint):
    type: str = field(default=PaymentInstrumentType.ACCOUNT)
    account_number: str = field(default=None)
    ifsc: str = field(default=None)

    @staticmethod
    def build_account_constraint(account_number: str, ifsc: str):
        return AccountConstraint(account_number=account_number,
                                 ifsc=ifsc,
                                 type=PaymentInstrumentType.ACCOUNT)
