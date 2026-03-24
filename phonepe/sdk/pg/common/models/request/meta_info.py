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


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class MetaInfo:
    udf1: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf2: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf3: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf4: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf5: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf6: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf7: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf8: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf9: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf10: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf11: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf12: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf13: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf14: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    udf15: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))

    _FREE_MAX = 256
    _RESTRICTED_MAX = 50
    _RESTRICTED_PATTERN = re.compile(r'^[a-zA-Z0-9_\- @.+]*$')

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
        MetaInfo._validate_size("udf1", udf1, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf2", udf2, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf3", udf3, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf4", udf4, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf5", udf5, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf6", udf6, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf7", udf7, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf8", udf8, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf9", udf9, MetaInfo._FREE_MAX)
        MetaInfo._validate_size("udf10", udf10, MetaInfo._FREE_MAX)
        MetaInfo._validate_size_and_pattern("udf11", udf11, MetaInfo._RESTRICTED_MAX)
        MetaInfo._validate_size_and_pattern("udf12", udf12, MetaInfo._RESTRICTED_MAX)
        MetaInfo._validate_size_and_pattern("udf13", udf13, MetaInfo._RESTRICTED_MAX)
        MetaInfo._validate_size_and_pattern("udf14", udf14, MetaInfo._RESTRICTED_MAX)
        MetaInfo._validate_size_and_pattern("udf15", udf15, MetaInfo._RESTRICTED_MAX)
        return MetaInfo(
            udf1=udf1, udf2=udf2, udf3=udf3, udf4=udf4, udf5=udf5,
            udf6=udf6, udf7=udf7, udf8=udf8, udf9=udf9, udf10=udf10,
            udf11=udf11, udf12=udf12, udf13=udf13, udf14=udf14, udf15=udf15,
        )
