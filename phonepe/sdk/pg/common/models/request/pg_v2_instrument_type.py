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

from enum import Enum


class PgV2InstrumentType(str, Enum):
    UPI_COLLECT = "UPI_COLLECT"
    UPI_INTENT = "UPI_INTENT"
    PPE_INTENT = "PPE_INTENT"
    UPI_QR = "UPI_QR"
    CARD = "CARD"
    TOKEN = "TOKEN"
    NET_BANKING = "NET_BANKING"
    UPI_AUTO_PAY = "UPI_AUTO_PAY"
