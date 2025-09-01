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

from phonepe.sdk.pg.common.models.request.instruments.payment_v2_instrument import PaymentV2Instrument
from phonepe.sdk.pg.payments.v2.models.request.merchant_urls import MerchantUrls
from phonepe.sdk.pg.common.models.request.payment_flow import PaymentFlow
from phonepe.sdk.pg.common.models.payment_flow_type import PaymentFlowType


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class PgPaymentFlow(PaymentFlow):
    type: str = field(default=PaymentFlowType.PG)
    payment_mode: PaymentV2Instrument = field(default=None)
    merchant_urls: MerchantUrls = field(default=None)
