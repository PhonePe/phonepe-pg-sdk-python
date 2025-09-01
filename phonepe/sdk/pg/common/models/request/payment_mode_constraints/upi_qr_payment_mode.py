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

from dataclasses import field, dataclass

from dataclasses_json import dataclass_json, LetterCase
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.payment_mode_constraint import PaymentModeConstraint

from phonepe.sdk.pg.common.models.request.pg_v2_instrument_type import (
    PgV2InstrumentType,
)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class UpiQrPaymentModeConstraint(PaymentModeConstraint):
    type: PgV2InstrumentType = field(default=PgV2InstrumentType.UPI_QR)
