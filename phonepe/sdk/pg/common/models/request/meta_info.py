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
import re
from typing import Optional

from dataclasses_json import dataclass_json, LetterCase, config

_EXCLUDE_NONE = config(exclude=lambda x: x is None)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class MetaInfo:
    udf1: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf2: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf3: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf4: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf5: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf6: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf7: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf8: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf9: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf10: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf11: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf12: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf13: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf14: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)
    udf15: Optional[str] = field(default=None, metadata=_EXCLUDE_NONE)

    _FREE_MAX = 256
    _RESTRICTED_MAX = 50
    _RESTRICTED_PATTERN = re.compile(r'^[a-zA-Z0-9_\- @.+]*$')

    def __post_init__(self):
        for i in range(1, 11):
            MetaInfo._validate_size(f"udf{i}", getattr(self, f"udf{i}"), MetaInfo._FREE_MAX)
        for i in range(11, 16):
            MetaInfo._validate_size_and_pattern(f"udf{i}", getattr(self, f"udf{i}"), MetaInfo._RESTRICTED_MAX)

    @staticmethod
    def _validate_size(field_name: str, value: str, max_len: int):
        if value is not None and len(value) > max_len:
            raise ValueError(f"{field_name} exceeds maximum allowed size of {max_len} characters")

    @staticmethod
    def _validate_size_and_pattern(field_name: str, value: str, max_len: int):
        if value is None:
            return
        if len(value) > max_len:
            raise ValueError(f"{field_name} exceeds maximum allowed size of {max_len} characters")
        if not MetaInfo._RESTRICTED_PATTERN.match(value):
            raise ValueError(
                f"{field_name} should only contain alphanumeric characters, underscores, hyphens, spaces, @, ., and +"
            )

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
        fields = locals()
        for i in range(1, 11):
            MetaInfo._validate_size(f"udf{i}", fields[f"udf{i}"], MetaInfo._FREE_MAX)
        for i in range(11, 16):
            MetaInfo._validate_size_and_pattern(f"udf{i}", fields[f"udf{i}"], MetaInfo._RESTRICTED_MAX)
        return MetaInfo(
            udf1=udf1, udf2=udf2, udf3=udf3, udf4=udf4, udf5=udf5,
            udf6=udf6, udf7=udf7, udf8=udf8, udf9=udf9, udf10=udf10,
            udf11=udf11, udf12=udf12, udf13=udf13, udf14=udf14, udf15=udf15,
        )
