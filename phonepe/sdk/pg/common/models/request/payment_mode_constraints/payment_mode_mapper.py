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

from phonepe.sdk.pg.common.models.request.payment_mode_constraints.card_payment_mode import (
    CardPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.net_banking_payment_mode import (
    NetBankingPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.payment_mode_constraint import PaymentModeConstraint
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.upi_collect_payment_mode import (
    UpiCollectPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.upi_intent_payment_mode import (
    UpiIntentPaymentModeConstraint,
)
from phonepe.sdk.pg.common.models.request.payment_mode_constraints.upi_qr_payment_mode import (
    UpiQrPaymentModeConstraint,
)

from phonepe.sdk.pg.common.models.request.pg_v2_instrument_type import (
    PgV2InstrumentType,
)

PAYMENT_MODE_MAPPER = {
    PgV2InstrumentType.CARD: CardPaymentModeConstraint,
    PgV2InstrumentType.UPI_INTENT: UpiIntentPaymentModeConstraint,
    PgV2InstrumentType.UPI_COLLECT: UpiCollectPaymentModeConstraint,
    PgV2InstrumentType.UPI_QR: UpiQrPaymentModeConstraint,
    PgV2InstrumentType.NET_BANKING: NetBankingPaymentModeConstraint,
}


def map_to_payment_mode(
        payment_mode_object: Union[dict, PaymentModeConstraint]
) -> Union[dict, PaymentModeConstraint]:
    """
    Maps a given dictionary or PaymentMode object to its corresponding subclass based on the 'type' field.

    Args:
        payment_mode_object (Union[dict, PaymentModeConstraint]): The input object (either a dictionary or an already
        deserialized PaymentMode object).

    Returns:
        Union[dict, PaymentModeConstraint]: The mapped PaymentMode subclass or the original object if no mapping exists.
    """

    # If the object is already a PaymentModeConstraint type, return it as-is
    if isinstance(payment_mode_object, PaymentModeConstraint):
        return payment_mode_object

    if payment_mode_object and isinstance(payment_mode_object, dict):
        payment_mode_type = payment_mode_object.get("type")

        if payment_mode_type and PAYMENT_MODE_MAPPER.get(payment_mode_type):
            payment_mode_class = PAYMENT_MODE_MAPPER[payment_mode_type]
            return payment_mode_class.from_dict(payment_mode_object)

    return payment_mode_object
