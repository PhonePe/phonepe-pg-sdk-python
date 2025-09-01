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

import hashlib


def is_callback_valid(username: str, password: str, response_header: str) -> bool:
    to_hash_string = f"{username}:{password}"
    sha256hash = str(hashlib.sha256(to_hash_string.encode()).hexdigest())
    return sha256hash == response_header


def calculate_hash(*args, **kwargs):
    return hash(str(args) + str(kwargs))  # calculates hash of all the arguments
