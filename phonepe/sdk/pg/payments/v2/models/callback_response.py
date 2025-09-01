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

from phonepe.sdk.pg.payments.v2.models.response.callback_data import CallbackData
from phonepe.sdk.pg.payments.v2.models.response.callback_type import CallbackType


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CallbackResponse:
    type: Optional[CallbackType] = field(default=None)
    event: Optional[str] = field(default=None)
    payload: Optional[CallbackData] = field(default=None)
