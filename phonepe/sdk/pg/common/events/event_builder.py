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

import time
from typing import Union

from phonepe.sdk.pg.common.events.models.base_event import BaseEvent
from phonepe.sdk.pg.common.events.models.enums.event_state import EventState
from phonepe.sdk.pg.common.events.models.enums.event_type import EventType
from phonepe.sdk.pg.common.events.models.enums.flow_type import FlowType
from phonepe.sdk.pg.common.events.models.event_data import EventData
from phonepe.sdk.pg.common.exceptions import PhonePeException
from phonepe.sdk.pg.payments.v2.models.request.create_sdk_order_request import (
    CreateSdkOrderRequest,
)
from phonepe.sdk.pg.common.models.request.refund_request import RefundRequest
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import (
    StandardCheckoutPayRequest,
)
from phonepe.sdk.pg.common.models.request.pg_payment_request import PgPaymentRequest
from phonepe.sdk.pg.subscription.v2.models.request.subscription_redemption_payment_flow import (
    SubscriptionRedemptionPaymentFlow,
)
from phonepe.sdk.pg.subscription.v2.models.request.subscription_setup_payment_flow import (
    SubscriptionSetupPaymentFlow,
)


def build_init_client_event(
    event_name: EventType, flow_type: FlowType = None
) -> BaseEvent:
    return BaseEvent(
        event_name=event_name,
        event_time=int(time.time()),
        data=EventData(event_state=EventState.INITIATED, flow_type=flow_type),
    )


def build_standard_checkout_pay_event(
    event_state: EventState,
    event_name: EventType,
    standard_checkout_pay_request: StandardCheckoutPayRequest,
    api_path: str,
    exception: Union[PhonePeException, Exception] = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        merchant_order_id=standard_checkout_pay_request.merchant_order_id,
        event_time=int(time.time()),
        data=EventData(
            event_state=event_state,
            amount=standard_checkout_pay_request.amount,
            flow_type=FlowType.PG_CHECKOUT,
            api_path=api_path,
            expire_after=standard_checkout_pay_request.expire_after,
        ),
    )

    return populate_phonepe_exception_fields(event, exception)


def build_custom_checkout_pay_event(
    event_state: EventState,
    custom_checkout_pay_request: PgPaymentRequest,
    api_path: str,
    event_name: EventType,
    exception: Union[PhonePeException, Exception] = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        merchant_order_id=custom_checkout_pay_request.merchant_order_id,
        event_time=int(time.time()),
        data=EventData(
            event_state=event_state,
            amount=custom_checkout_pay_request.amount,
            flow_type=FlowType.PG,
            api_path=api_path,
            payment_instrument=getattr(
                getattr(custom_checkout_pay_request.payment_flow, "payment_mode", None),
                "type",
                None,
            ),  # getattr to prevent NPE
            target_app=getattr(
                getattr(custom_checkout_pay_request.payment_flow, "payment_mode", None),
                "target_app",
                None,
            ),
            expire_after=custom_checkout_pay_request.expire_after,
            device_context=custom_checkout_pay_request.device_context,
        ),
    )

    return populate_phonepe_exception_fields(event, exception)


def build_order_status_event(
    event_state: EventState,
    merchant_order_id: str,
    flow_type: FlowType,
    api_path: str,
    event_name: EventType,
    exception: Exception = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        merchant_order_id=merchant_order_id,
        event_time=int(time.time()),
        data=EventData(event_state=event_state, flow_type=flow_type, api_path=api_path),
    )
    return populate_phonepe_exception_fields(event, exception)


def build_refund_event(
    event_state: EventState,
    refund_request: RefundRequest,
    event_name: EventType,
    flow_type: FlowType,
    api_path: str,
    exception: Exception = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        merchant_order_id=refund_request.original_merchant_order_id,
        event_time=int(time.time()),
        data=EventData(
            event_state=event_state,
            amount=refund_request.amount,
            api_path=api_path,
            merchant_refund_id=refund_request.merchant_refund_id,
            original_merchant_order_id=refund_request.original_merchant_order_id,
            flow_type=flow_type,
        ),
    )
    return populate_phonepe_exception_fields(event, exception)


def build_refund_status_event(
    event_state: EventState,
    merchant_refund_id: str,
    flow_type: FlowType,
    api_path: str,
    event_name: EventType,
    exception: Exception = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        event_time=int(time.time()),
        data=EventData(
            merchant_refund_id=merchant_refund_id,
            event_state=event_state,
            api_path=api_path,
            flow_type=flow_type,
        ),
    )
    return populate_phonepe_exception_fields(event, exception)


def build_create_sdk_order_event(
    event_state: EventState,
    create_sdk_order_request: CreateSdkOrderRequest,
    api_path: str,
    event_name: EventType,
    flow_type: FlowType,
    exception: Exception = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        event_time=int(time.time()),
        merchant_order_id=create_sdk_order_request.merchant_order_id,
        data=EventData(
            amount=create_sdk_order_request.amount,
            event_state=event_state,
            api_path=api_path,
            flow_type=flow_type,
            expire_after=create_sdk_order_request.expire_after,
        ),
    )

    return populate_phonepe_exception_fields(event, exception)


def build_transaction_status_event(
    event_state: EventState,
    transaction_id: str,
    api_path: str,
    event_name: EventType,
    flow_type: FlowType,
    exception: Exception = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        event_time=int(time.time()),
        data=EventData(
            transaction_id=transaction_id,
            event_state=event_state,
            api_path=api_path,
            flow_type=flow_type,
        ),
    )

    return populate_phonepe_exception_fields(event, exception)


def build_oauth_event_used_cached_token_failed(
    cached_token_issued_at: int,
    cached_token_expires_at: int,
    fetch_attempt_time: int,
    api_path: str,
    exception: Exception = None,
):
    event = BaseEvent(
        event_name=EventType.OAUTH_FETCH_FAILED_USED_CACHED_TOKEN,
        event_time=int(time.time()),
        data=EventData(
            api_path=api_path,
            event_state=EventState.FAILED,
            cached_token_issued_at=cached_token_issued_at,
            cached_token_expires_at=cached_token_expires_at,
            token_fetch_attempt_timestamp=fetch_attempt_time,
        ),
    )

    return populate_phonepe_exception_fields(event, exception)


def build_callback_serialization_failed_event(
    event_state: EventState,
    event_name: EventType,
    flow_type: FlowType,
    exception: Exception = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        event_time=int(time.time()),
        data=EventData(event_state=event_state, flow_type=flow_type),
    )

    return populate_phonepe_exception_fields(event, exception)


def populate_phonepe_exception_fields(event: BaseEvent, exception: Exception):
    if exception is None:
        return event

    # Extract exception data
    event.data.inbuilt_exception_repr = repr(exception)

    event.data.exception_message = getattr(
        exception, "message", None
    )  # None if message field is absent
    event.data.exception_code = getattr(exception, "code", None)
    event.data.exception_http_status_code = getattr(exception, "http_status_code", None)
    event.data.exception_data = getattr(exception, "data", None)
    event.data.exception_class = exception.__class__.__name__
    return event


def build_subscription_setup_event(
    event_state: EventState,
    setup_request: PgPaymentRequest,
    api_path: str,
    event_name: EventType,
    exception: Exception = None,
) -> BaseEvent:
    event_data = EventData(
        event_state=event_state,
        api_path=api_path,
        flow_type=FlowType.SUBSCRIPTION,
        order_expire_at=setup_request.expire_at,
        device_context=setup_request.device_context,
        amount=setup_request.amount,
    )
    if isinstance(setup_request.payment_flow, SubscriptionSetupPaymentFlow):
        event_data.payment_instrument = getattr(
            getattr(setup_request.payment_flow, "payment_mode", None), "type", None
        )
        event_data.target_app = getattr(
            getattr(setup_request.payment_flow, "payment_mode", None),
            "target_app",
            None,
        )
        event_data.subscription_expire_at = getattr(
            getattr(setup_request, "payment_flow", None), "expire_at", None
        )
        event_data.merchant_subscription_id = getattr(
            getattr(setup_request, "payment_flow", None),
            "merchant_subscription_id",
            None,
        )
    event = BaseEvent(
        merchant_order_id=setup_request.merchant_order_id,
        event_time=int(time.time()),
        event_name=event_name,
        data=event_data,
    )

    return populate_phonepe_exception_fields(event, exception)


def build_subscription_notify_event(
    event_state: EventState,
    notify_request: PgPaymentRequest,
    api_path: str,
    event_name: EventType,
    exception: Exception = None,
) -> BaseEvent:
    payment_flow = SubscriptionRedemptionPaymentFlow(notify_request.payment_flow.type)
    event = BaseEvent(
        event_name=event_name,
        event_time=int(time.time()),
        merchant_order_id=notify_request.merchant_order_id,
        data=EventData(
            event_state=event_state,
            api_path=api_path,
            amount=notify_request.amount,
            order_expire_at=notify_request.expire_at,
            flow_type=FlowType.SUBSCRIPTION,
            merchant_subscription_id=payment_flow.merchant_subscription_id,
        ),
    )

    return populate_phonepe_exception_fields(event, exception)


def build_subscription_redeem_event(
    event_state: EventState,
    merchant_order_id: str,
    api_path: str,
    event_name: EventType,
    exception: Exception = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        event_time=int(time.time()),
        merchant_order_id=merchant_order_id,
        data=EventData(
            flow_type=FlowType.SUBSCRIPTION, event_state=event_state, api_path=api_path
        ),
    )

    return populate_phonepe_exception_fields(event, exception)


def build_subscription_event(
    event_state: EventState,
    api_path: str,
    event_name: EventType,
    merchant_subscription_id: str = None,
    merchant_order_id: str = None,
    exception: Exception = None,
) -> BaseEvent:
    event = BaseEvent(
        event_name=event_name,
        event_time=int(time.time()),
        merchant_order_id=merchant_order_id,
        data=EventData(
            merchant_subscription_id=merchant_subscription_id,
            event_state=event_state,
            api_path=api_path,
            flow_type=FlowType.SUBSCRIPTION,
        ),
    )
    return populate_phonepe_exception_fields(event, exception)
