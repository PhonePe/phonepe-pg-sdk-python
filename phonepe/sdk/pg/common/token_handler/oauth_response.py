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

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class OauthResponse:
    expires_at: int = field(default=None)
    issued_at: int = field(default=None)
    access_token: str = field(default=None)
    token_type: str = field(default=None)
    encrypted_access_token: str = field(default=None)
    session_expires_at: str = field(default=None)
    expires_in: int = field(default=None)
    refresh_token: str = field(default=None)
