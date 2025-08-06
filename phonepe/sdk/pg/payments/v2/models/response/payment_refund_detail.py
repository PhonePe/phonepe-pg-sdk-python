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
from typing import Optional, List

from dataclasses_json import dataclass_json, LetterCase

from phonepe.sdk.pg.payments.v2.models.request.pg_v2_instrument_type import PgV2InstrumentType
from phonepe.sdk.pg.payments.v2.models.response.instrument_combo import InstrumentCombo
from phonepe.sdk.pg.common.models.response.payment_instruments.payment_instrument_mapper import \
    map_to_payment_instrument
from phonepe.sdk.pg.common.models.response.payment_instruments.payment_instrument_v2 import PaymentInstrumentV2
from phonepe.sdk.pg.common.models.response.rails.payment_rail import PaymentRail
from phonepe.sdk.pg.common.models.response.rails.rail_mapper import map_to_payment_rail


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class PaymentRefundDetail:
    transaction_id: Optional[str] = field(default=None)
    payment_mode: Optional[PgV2InstrumentType] = field(default=None)
    timestamp: Optional[int] = field(default=None)
    amount: Optional[int] = field(default=None)
    state: Optional[str] = field(default=None)
    error_code: Optional[str] = field(default=None)
    detailed_error_code: Optional[str] = field(default=None)
    instrument: Optional[PaymentInstrumentV2] = field(default=None)
    rail: Optional[PaymentRail] = field(default=None)
    split_instruments: Optional[List[InstrumentCombo]] = field(default=None)

    def __post_init__(self):
        self.instrument = map_to_payment_instrument(instrument_object=self.instrument)
        self.rail = map_to_payment_rail(rail_object=self.rail)
