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

PAY_API = "/checkout/v2/pay"
REFUND_API = "/payments/v2/refund"
ORDER_STATUS_API = "/checkout/v2/order/{merchant_order_id}/status"
REFUND_STATUS_API = "/payments/v2/refund/{merchant_refund_id}/status"
CREATE_ORDER_API = "/checkout/v2/sdk/order"
TRANSACTION_STATUS_API = "/checkout/v2/transaction/{transaction_id}/status"
ORDER_DETAILS = "details"
