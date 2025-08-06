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

from typing import Union

from phonepe.sdk.pg.common.models.response.rails.payment_rail import PaymentRail
from phonepe.sdk.pg.common.models.response.rails.payment_rail_type import PaymentRailType
from phonepe.sdk.pg.common.models.response.rails.pg_payment_rail import PgPaymentRail
from phonepe.sdk.pg.common.models.response.rails.ppi_evg_payment_rail import PpiEgvPaymentRail
from phonepe.sdk.pg.common.models.response.rails.ppi_wallet_payment_rail import PpiWalletPaymentRail
from phonepe.sdk.pg.common.models.response.rails.upi_payment_rail import UpiPaymentRail

RAIL_MAPPER = {PaymentRailType.UPI: UpiPaymentRail,
               PaymentRailType.PG: PgPaymentRail,
               PaymentRailType.PPI_EGV: PpiEgvPaymentRail,
               PaymentRailType.PPI_WALLET: PpiWalletPaymentRail}


def map_to_payment_rail(rail_object: Union[dict, PaymentRail]) -> Union[dict, PaymentRail]:
    if rail_object and type(rail_object) == dict and RAIL_MAPPER.get(rail_object.get("type")):
        rail_type = RAIL_MAPPER.get(rail_object.get("type"))
        return rail_type.from_dict(rail_object)
    return rail_object
