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

from typing import List
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase

from phonepe.sdk.pg.common.models.request.payment_flow import PaymentFlow
from phonepe.sdk.pg.common.models.request.device_context import DeviceContext
from phonepe.sdk.pg.common.models.request.instrument_constraint import (
    InstrumentConstraint,
)

from phonepe.sdk.pg.common.models.request.instruments.card_payment_v2_instrument import (
    CardPaymentV2Instrument,
)
from phonepe.sdk.pg.common.models.request.instruments.collect_payment_v2_instrument import (
    CollectPaymentV2Instrument,
)
from phonepe.sdk.pg.common.models.request.instruments.expiry import Expiry
from phonepe.sdk.pg.common.models.request.instruments.intent_payment_v2_instrument import (
    IntentPaymentV2Instrument,
)
from phonepe.sdk.pg.common.models.request.instruments.net_banking_payment_v2_instrument import (
    NetBankingPaymentV2Instrument,
)
from phonepe.sdk.pg.common.models.request.instruments.new_card_details import (
    NewCardDetails,
)
from phonepe.sdk.pg.common.models.request.instruments.phone_number_collect_payment_details import (
    PhoneNumberCollectPaymentDetails,
)
from phonepe.sdk.pg.common.models.request.instruments.token_details import TokenDetails
from phonepe.sdk.pg.common.models.request.instruments.token_payment_v2_instrument import (
    TokenPaymentV2Instrument,
)
from phonepe.sdk.pg.common.models.request.instruments.upi_qr_payment_v2_instrument import (
    UpiQrPaymentV2Instrument,
)
from phonepe.sdk.pg.common.models.request.instruments.vpa_collect_payment_details import (
    VpaCollectPaymentDetails,
)
from phonepe.sdk.pg.payments.v2.models.request.merchant_urls import MerchantUrls
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.payments.v2.models.request.pg_payment_flow import PgPaymentFlow

from phonepe.sdk.pg.subscription.v2.models.request.amount_type import AmountType
from phonepe.sdk.pg.subscription.v2.models.request.auth_workflow_type import (
    AuthWorkflowType,
)
from phonepe.sdk.pg.subscription.v2.models.request.frequency import Frequency
from phonepe.sdk.pg.subscription.v2.models.request.redemption_retry_strategy import (
    RedemptionRetryStrategy,
)
from phonepe.sdk.pg.subscription.v2.models.request.subscription_redemption_payment_flow import (
    SubscriptionRedemptionPaymentFlow,
)
from phonepe.sdk.pg.subscription.v2.models.request.subscription_setup_payment_flow import (
    SubscriptionSetupPaymentFlow,
)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class PgPaymentRequest:
    """
    Represents a payment request to be sent to the payment gateway.
    """

    merchant_order_id: str = field(default=None)
    amount: int = field(default=None)
    meta_info: MetaInfo = field(default=None)
    device_context: DeviceContext = field(default=None)
    payment_flow: PaymentFlow = field(default=None)
    constraints: List[InstrumentConstraint] = field(default=None)
    expire_after: int = field(default=None)
    expire_at: int = field(default=None)

    @staticmethod
    def build_upi_intent_pay_request(
        merchant_order_id: str,
        amount: int,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
        device_os: str = None,
        merchant_callback_scheme: str = None,
        target_app: str = None,
        expire_after: int = None,
    ):
        """
        Builds a payment request for UPI intent-based payment.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        amount : int
            Order amount in paise
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.
        device_os : str, optional
            The operating system of the device making the request.
        merchant_callback_scheme : str, optional
            The callback scheme for the merchant.
        target_app : str, optional
            The target application for UPI payment.
        expire_after : int, optional
            The expiry time in seconds(epoch) for the payment request.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            expire_after=expire_after,
            device_context=DeviceContext(
                device_os=device_os, merchant_callback_scheme=merchant_callback_scheme
            ),
            payment_flow=PgPaymentFlow(
                payment_mode=IntentPaymentV2Instrument(target_app=target_app)
            ),
        )

    @staticmethod
    def build_upi_collect_pay_via_vpa_request(
        merchant_order_id: str,
        amount: int,
        vpa: str,
        message: str,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
        expire_after: int = None,
    ):
        """
        Builds a payment request for UPI collect payment via VPA (Virtual Payment Address).

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        amount : int
            Order amount in paise
        vpa : str
            The Virtual Payment Address (VPA) for collecting payment.
        message : str
            The message to be sent to the user.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.
        expire_after : int, optional
            The expiry time in seconds for the payment request.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            payment_flow=PgPaymentFlow(
                payment_mode=CollectPaymentV2Instrument(
                    details=VpaCollectPaymentDetails(vpa=vpa), message=message
                )
            ),
            expire_after=expire_after,
        )

    @staticmethod
    def build_upi_collect_pay_via_phone_number_request(
        merchant_order_id: str,
        amount: int,
        phone_number: str,
        message: str,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
        expire_after: int = None,
    ):
        """
        Builds a payment request for UPI collect payment via phone number.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        amount : int
            Order amount in paise.
        phone_number : str
            The phone number for collecting payment.
        message : str
            The message to be sent to the user.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.
        expire_after : int, optional
            The expiry time in seconds for the payment request.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            payment_flow=PgPaymentFlow(
                payment_mode=CollectPaymentV2Instrument(
                    details=PhoneNumberCollectPaymentDetails(phone_number=phone_number),
                    message=message,
                )
            ),
            expire_after=expire_after,
        )

    @staticmethod
    def build_upi_qr_pay_request(
        merchant_order_id: str,
        amount: int,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
        expire_after: int = None,
    ):
        """
        Builds a payment request for UPI QR-based payments.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        amount : int
            Order amount in paise.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.
        expire_after : int, optional
            The expiry time in seconds for the payment request.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            payment_flow=PgPaymentFlow(payment_mode=UpiQrPaymentV2Instrument()),
            expire_after=expire_after,
        )

    @staticmethod
    def build_net_banking_pay_request(
        merchant_order_id: str,
        amount: int,
        bank_id: str,
        redirect_url: str,
        merchant_user_id: str = None,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
        expire_after: int = None,
    ):
        """
        Builds a payment request for net banking-based payments.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        amount : int
            Order amount in paise
        bank_id : str
            The bank identifier for the net banking transaction.
        redirect_url : str
            The URL to which the user will be redirected after payment.
        merchant_user_id : str, optional
            The unique identifier for the merchant user.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.
        expire_after : int, optional
            The expiry time in seconds for the payment request.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            payment_flow=PgPaymentFlow(
                payment_mode=NetBankingPaymentV2Instrument(
                    bank_id=bank_id, merchant_user_id=merchant_user_id
                ),
                merchant_urls=MerchantUrls(redirect_url=redirect_url),
            ),
            expire_after=expire_after,
        )

    @staticmethod
    def build_token_pay_request(
        merchant_order_id: str,
        amount: int,
        auth_mode: str,
        encryption_key_id: int,
        encrypted_token: str,
        encrypted_cvv: str,
        cryptogram: str,
        pan_suffix: str,
        expiry_month: str,
        expiry_year: str,
        redirect_url: str,
        card_holder_name: str = None,
        merchant_user_id: str = None,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
        expire_after: int = None,
    ):
        """
        Builds a payment request for token-based card payments.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        amount : int
            Order amount in paise
        auth_mode : str
            The authentication mode for the transaction.
        encryption_key_id : int
            The encryption key ID for encrypting card details.
        encrypted_token : str
            The encrypted payment token.
        encrypted_cvv : str
            The encrypted CVV of the card.
        cryptogram : str
            The cryptogram associated with the transaction.
        pan_suffix : str
            The suffix of the PAN (Primary Account Number).
        expiry_month : str
            The expiry month of the card.
        expiry_year : str
            The expiry year of the card.
        redirect_url : str
            The URL to which the user will be redirected after payment.
        card_holder_name : str, optional
            The name of the card holder.
        merchant_user_id : str, optional
            The unique identifier for the merchant user.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.
        expire_after : int, optional
            The expiry time in seconds for the payment request.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            payment_flow=PgPaymentFlow(
                payment_mode=TokenPaymentV2Instrument(
                    auth_mode=auth_mode,
                    merchant_user_id=merchant_user_id,
                    token_details=TokenDetails(
                        encrypted_token=encrypted_token,
                        encryption_key_id=encryption_key_id,
                        encrypted_cvv=encrypted_cvv,
                        cryptogram=cryptogram,
                        pan_suffix=pan_suffix,
                        card_holder_name=card_holder_name,
                        expiry=Expiry(month=expiry_month, year=expiry_year),
                    ),
                ),
                merchant_urls=MerchantUrls(redirect_url=redirect_url),
            ),
            expire_after=expire_after,
        )

    @staticmethod
    def build_card_pay_request(
        merchant_order_id: str,
        amount: int,
        auth_mode: str,
        encryption_key_id: int,
        encrypted_card_number: str,
        encrypted_cvv: str,
        expiry_month: str,
        expiry_year: str,
        card_holder_name: str,
        redirect_url: str,
        merchant_user_id: str = None,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
        expire_after: int = None,
    ):
        """
        Builds a payment request for card-based payments.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        amount : int
            Order amount in paise
        auth_mode : str
            The authentication mode for the transaction.
        encryption_key_id : int
            The encryption key ID for encrypting card details.
        encrypted_card_number : str
            The encrypted card number.
        encrypted_cvv : str
            The encrypted CVV of the card.
        expiry_month : str
            The expiry month of the card.
        expiry_year : str
            The expiry year of the card.
        card_holder_name : str
            The name of the card holder.
        redirect_url : str
            The URL to which the user will be redirected after payment.
        merchant_user_id : str, optional
            The unique identifier for the merchant user.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.
        expire_after : int, optional
            The expiry time in seconds for the payment request.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            payment_flow=PgPaymentFlow(
                payment_mode=CardPaymentV2Instrument(
                    auth_mode=auth_mode,
                    merchant_user_id=merchant_user_id,
                    card_details=NewCardDetails(
                        encryption_key_id=encryption_key_id,
                        encrypted_card_number=encrypted_card_number,
                        encrypted_cvv=encrypted_cvv,
                        card_holder_name=card_holder_name,
                        expiry=Expiry(month=expiry_month, year=expiry_year),
                    ),
                ),
                merchant_urls=MerchantUrls(redirect_url=redirect_url),
            ),
            expire_after=expire_after,
        )

    @staticmethod
    def build_subscription_setup_upi_intent(
        merchant_order_id: str,
        merchant_subscription_id: str,
        amount: int,
        max_amount: int,
        auth_workflow_type: AuthWorkflowType,
        amount_type: AmountType,
        frequency: Frequency,
        device_os: str = None,
        merchant_callback_scheme: str = None,
        target_app: str = None,
        order_expire_at: int = None,
        subscription_expire_at: int = None,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
    ):
        """
        Builds a payment request for UPI intent-based subscription setup.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        merchant_subscription_id : str
            Unique merchant reference subscription ID (used for subscription status).
        amount : int
            Order amount in paise
        max_amount : int
            The maximum amount allowed for the subscription.
        auth_workflow_type : AuthWorkflowType
            The authentication workflow type.
        amount_type : AmountType
            The type of amount (e.g., fixed or variable).
        frequency : Frequency
            The frequency of subscription payments.
        device_os : str, optional
            The operating system of the device making the request.
        merchant_callback_scheme : str, optional
            The callback scheme for the merchant.
        target_app : str, optional
            The target application for UPI payment.
        order_expire_at : int, optional
            The timestamp at which the order expires.
        subscription_expire_at : int, optional
            The timestamp at which the subscription expires.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            expire_at=order_expire_at,
            payment_flow=SubscriptionSetupPaymentFlow(
                merchant_subscription_id=merchant_subscription_id,
                amount_type=amount_type,
                auth_workflow_type=auth_workflow_type,
                expire_at=subscription_expire_at,
                payment_mode=IntentPaymentV2Instrument(target_app=target_app),
                frequency=frequency,
                max_amount=max_amount,
            ),
            device_context=DeviceContext(
                device_os=device_os, merchant_callback_scheme=merchant_callback_scheme
            ),
        )

    @staticmethod
    def build_subscription_setup_upi_collect(
        merchant_order_id: str,
        merchant_subscription_id: str,
        amount: int,
        max_amount: int,
        vpa: str,
        auth_workflow_type: AuthWorkflowType,
        amount_type: AmountType,
        frequency: Frequency,
        message: str = None,
        subscription_expire_at: int = None,
        order_expire_at: int = None,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
    ):
        """
        Builds a payment request for UPI collect-based subscription setup.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        merchant_subscription_id : str
            Unique merchant reference subscription ID - used for subscription status
        amount : int
            Order amount in paise.
        max_amount : int
            The maximum amount allowed for the subscription.
        vpa : str
            The Virtual Payment Address for the UPI collect.
        auth_workflow_type : AuthWorkflowType
            The authentication workflow type.
        amount_type : AmountType
            The type of amount (e.g., fixed or variable).
        frequency : Frequency
            The frequency of subscription payments.
        message : str, optional
            A custom message for the payment request.
        subscription_expire_at : int, optional
            The timestamp at which the subscription expires.
        order_expire_at : int, optional
            The timestamp at which the order expires.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            expire_at=order_expire_at,
            payment_flow=SubscriptionSetupPaymentFlow(
                merchant_subscription_id=merchant_subscription_id,
                amount_type=amount_type,
                auth_workflow_type=auth_workflow_type,
                expire_at=subscription_expire_at,
                payment_mode=CollectPaymentV2Instrument(
                    details=VpaCollectPaymentDetails(
                        vpa=vpa,
                    ),
                    message=message,
                ),
                frequency=frequency,
                max_amount=max_amount,
            ),
        )

    @staticmethod
    def build_subscription_notify_request(
        merchant_order_id: str,
        merchant_subscription_id: str,
        amount: int,
        redemption_retry_strategy: RedemptionRetryStrategy,
        auto_debit: bool = False,
        expire_at: int = None,
        meta_info: MetaInfo = None,
        constraints: List[InstrumentConstraint] = None,
    ):
        """
        Builds a payment request for subscription notifications and redemption.

        Parameters
        ----------
        merchant_order_id : str
            Unique merchant reference order ID (used for order status).
        merchant_subscription_id : str
            Unique merchant reference subscription ID - used for subscription status
        amount : int
            Order amount in paise
        redemption_retry_strategy : RedemptionRetryStrategy
            The strategy for retrying redemption attempts.
        auto_debit : bool, optional
            Whether the payment is automatic (default is False).
        expire_at : int, optional
            The timestamp at which the order expires.
        meta_info : MetaInfo, optional
            Additional metadata for the payment request.
        constraints : List[InstrumentConstraint], optional
            Constraints on the payment instrument.

        Returns
        -------
        PgPaymentRequest
            The constructed payment request object.
        """
        return PgPaymentRequest(
            merchant_order_id=merchant_order_id,
            amount=amount,
            meta_info=meta_info,
            constraints=constraints,
            expire_at=expire_at,
            payment_flow=SubscriptionRedemptionPaymentFlow(
                merchant_subscription_id=merchant_subscription_id,
                auto_debit=auto_debit,
                redemption_retry_strategy=redemption_retry_strategy,
            ),
        )
