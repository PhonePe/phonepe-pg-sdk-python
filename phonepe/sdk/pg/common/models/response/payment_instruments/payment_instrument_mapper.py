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

from phonepe.sdk.pg.common.models.request.payment_mode_constraints.payment_mode_constraint import PaymentModeConstraint
from phonepe.sdk.pg.common.models.response.payment_instruments.account_payment_instrument_v2 import (
    AccountPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.credit_card_payment_instrument_v2 import (
    CreditCardPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.debit_card_payment_instrument_v2 import (
    DebitCardPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.egv_payment_instrument_v2 import (
    EvgPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.net_banking_payment_instrument_v2 import (
    NetBankingPaymentInstrumentV2,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.payment_instrument_v2_type import (
    PaymentInstrumentV2Type,
)
from phonepe.sdk.pg.common.models.response.payment_instruments.wallet_payment_instrument_v2 import (
    WalletPaymentInstrumentV2,
)

INSTRUMENT_MAPPER = {
    PaymentInstrumentV2Type.ACCOUNT: AccountPaymentInstrumentV2,
    PaymentInstrumentV2Type.NET_BANKING: NetBankingPaymentInstrumentV2,
    PaymentInstrumentV2Type.EGV: EvgPaymentInstrumentV2,
    PaymentInstrumentV2Type.WALLET: WalletPaymentInstrumentV2,
    PaymentInstrumentV2Type.CREDIT_CARD: CreditCardPaymentInstrumentV2,
    PaymentInstrumentV2Type.DEBIT_CARD: DebitCardPaymentInstrumentV2,
}


def map_to_payment_instrument(
        instrument_object: Union[dict, PaymentModeConstraint]
) -> Union[dict, PaymentModeConstraint]:
    if (
            instrument_object
            and type(instrument_object) == dict
            and INSTRUMENT_MAPPER.get(instrument_object.get("type"))
    ):
        instrument_type = INSTRUMENT_MAPPER.get(instrument_object.get("type"))
        return instrument_type.from_dict(instrument_object)
    return instrument_object
