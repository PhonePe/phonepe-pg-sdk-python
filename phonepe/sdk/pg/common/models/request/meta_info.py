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


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class MetaInfo:
    udf1: Optional[str] = field(default=None)
    udf2: Optional[str] = field(default=None)
    udf3: Optional[str] = field(default=None)
    udf4: Optional[str] = field(default=None)
    udf5: Optional[str] = field(default=None)
    udf6: Optional[str] = field(default=None)
    udf7: Optional[str] = field(default=None)
    udf8: Optional[str] = field(default=None)
    udf9: Optional[str] = field(default=None)
    udf10: Optional[str] = field(default=None)
    udf11: Optional[str] = field(default=None)
    udf12: Optional[str] = field(default=None)
    udf13: Optional[str] = field(default=None)
    udf14: Optional[str] = field(default=None)
    udf15: Optional[str] = field(default=None)

    @staticmethod
    def build_meta_info(
        udf1: str,
        udf2: str = None,
        udf3: str = None,
        udf4: str = None,
        udf5: str = None,
        udf6: str = None,
        udf7: str = None,
        udf8: str = None,
        udf9: str = None,
        udf10: str = None,
        udf11: str = None,
        udf12: str = None,
        udf13: str = None,
        udf14: str = None,
        udf15: str = None,
    ):
        return MetaInfo(
            udf1=udf1, udf2=udf2, udf3=udf3, udf4=udf4, udf5=udf5,
            udf6=udf6, udf7=udf7, udf8=udf8, udf9=udf9, udf10=udf10,
            udf11=udf11, udf12=udf12, udf13=udf13, udf14=udf14, udf15=udf15,
        )
