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

import json

from phonepe.sdk.pg.common.base_client import BaseClient
from phonepe.sdk.pg.common.constants.headers import (
    SUBSCRIPTION_API_VERSION,
    SOURCE_VERSION,
)
from phonepe.sdk.pg.common.events.event_builder import (
    build_init_client_event,
    build_order_status_event,
    build_refund_status_event,
    build_transaction_status_event,
    build_refund_event,
    build_subscription_setup_event,
    build_subscription_notify_event,
    build_subscription_redeem_event,
    build_subscription_event,
    build_callback_serialization_failed_event,
)
from phonepe.sdk.pg.common.events.models.enums.event_state import EventState
from phonepe.sdk.pg.common.events.models.enums.event_type import EventType
from phonepe.sdk.pg.common.events.models.enums.flow_type import FlowType
from phonepe.sdk.pg.common.exceptions import PhonePeException
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType
from phonepe.sdk.pg.common.models.request.pg_payment_request import PgPaymentRequest
from phonepe.sdk.pg.common.models.request.refund_request import RefundRequest
from phonepe.sdk.pg.common.models.response.order_status_response import (
    OrderStatusResponse,
)
from phonepe.sdk.pg.common.models.response.pg_payment_response import PgPaymentResponse
from phonepe.sdk.pg.common.models.response.refund_response import RefundResponse
from phonepe.sdk.pg.common.models.response.refund_status_response import (
    RefundStatusResponse,
)
from phonepe.sdk.pg.common.utils.hash_utils import calculate_hash, is_callback_valid
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v2.models.callback_response import CallbackResponse
from phonepe.sdk.pg.subscription.v2.models.request.subscription_redeem_request_v2 import (
    SubscriptionRedeemRequestV2,
)
from phonepe.sdk.pg.subscription.v2.models.response.subscription_redeem_response_v2 import (
    SubscriptionRedeemResponseV2,
)
from phonepe.sdk.pg.subscription.v2.models.response.subscription_status_response_v2 import (
    SubscriptionStatusResponseV2,
)
from phonepe.sdk.pg.subscription.v2.models.subscription_constants import (
    SETUP_API,
    NOTIFY_API,
    REDEEM_API,
    SUBSCRIPTION_STATUS_API,
    ORDER_STATUS_API,
    CANCEL_SUBSCRIPTION_API,
    TRANSACTION_STATUS_API,
    REFUND_API,
    REFUND_STATUS_API,
)


from typing import Dict
class SubscriptionClient(BaseClient):
    """
    The SubscriptionClient client class provides methods for interacting with the PhonePe APIs.
    """

    _cached_instances: Dict[str, BaseClient] = {}
    headers = {SOURCE_VERSION: SUBSCRIPTION_API_VERSION}

    def __init__(
        self,
        client_id: str,
        client_version: int,
        client_secret: str,
        env: Env,
        should_publish_events: bool = True,
    ):
        """
        Initialize the SubscriptionClient class.

        Parameters
        ----------
        client_id: str
            Unique client ID assigned to merchant by PhonePe
        client_secret: str
            Secret provided by PhonePe
        client_version: str
            The client version used for secure transactions
        env: str
            Environment (SANDBOX or PRODUCTION)
        should_publish_events: bool
            Indicates if events should be published to PhonePe
        """
        should_publish_events = should_publish_events and env == Env.PRODUCTION
        super().__init__(
            client_id, client_secret, client_version, env, should_publish_events
        )

    @staticmethod
    def get_instance(
        client_id: str,
        client_secret: str,
        client_version: int,
        env: Env,
        should_publish_events: bool = True,
    ):
        """
        Get or create an instance of SubscriptionClient class.

        Parameters
        ----------
        client_id: str
            Unique client ID assigned to merchant by PhonePe
        client_secret: str
            Secret provided by PhonePe
        client_version: str
            The client version used for secure transactions
        env: str
            Environment (SANDBOX or PRODUCTION)
        should_publish_events: bool
            Indicates if events should be published to PhonePe

        Returns
        ----------
        SubscriptionClient:
            An instance of SubscriptionClient
        """
        should_publish_events = should_publish_events and env == Env.PRODUCTION
        requested_client_sha = calculate_hash(
            str(client_id),
            str(client_version),
            str(client_secret),
            str(env),
            str(should_publish_events),
            str(FlowType.SUBSCRIPTION),
        )
        if requested_client_sha in SubscriptionClient._cached_instances.keys():
            return SubscriptionClient._cached_instances[requested_client_sha]

        new_instance = SubscriptionClient(
            client_id=client_id,
            client_version=client_version,
            client_secret=client_secret,
            env=env,
            should_publish_events=should_publish_events,
        )
        SubscriptionClient._cached_instances[requested_client_sha] = new_instance
        init_event = build_init_client_event(
            flow_type=FlowType.SUBSCRIPTION,
            event_name=EventType.SUBSCRIPTION_CLIENT_INITIALIZED,
        )
        new_instance.event_publisher.send(init_event)
        return SubscriptionClient._cached_instances[requested_client_sha]

    def setup(self, request: PgPaymentRequest) -> PgPaymentResponse:
        """
        Setup the subscription based on the given merchant requirements.

        Parameters
        ----------
        request: PgPaymentRequest
            Request built using PgPaymentRequest builder

        Returns
        ----------
        PgPaymentResponse:
            Contains the state of the requested setup
        """
        url = SETUP_API
        headers = self.headers
        try:
            response = self._request_via_auth_refresh(
                method=HttpMethodType.POST,
                data=request.to_json(),
                url=url,
                headers=headers,
                response_obj=PgPaymentResponse,
            )
            self.event_publisher.send(
                build_subscription_setup_event(
                    event_state=EventState.SUCCESS,
                    setup_request=request,
                    api_path=url,
                    event_name=EventType.SETUP_SUCCESS,
                )
            )
            return response
        except Exception as exception:
            self.event_publisher.send(
                build_subscription_setup_event(
                    event_state=EventState.FAILED,
                    setup_request=request,
                    api_path=url,
                    event_name=EventType.SETUP_FAILED,
                    exception=exception,
                )
            )
            raise exception

    def notify(self, request: PgPaymentRequest) -> PgPaymentResponse:
        """
        Send notify information to PhonePe.

        Parameters
        ----------
        request: PgPaymentRequest.SubscriptionNotifyRequestBuilder
            Request built using PgPaymentRequest.SubscriptionNotifyRequestBuilder()

        Returns
        ----------
        PgPaymentResponse:
            Contains the state of the requested notify
        """
        url = NOTIFY_API
        headers = self.headers
        try:
            response = self._request_via_auth_refresh(
                method=HttpMethodType.POST,
                data=request.to_json(),
                url=url,
                headers=headers,
                response_obj=PgPaymentResponse,
            )
            self.event_publisher.send(
                build_subscription_notify_event(
                    event_state=EventState.SUCCESS,
                    notify_request=request,
                    api_path=url,
                    event_name=EventType.NOTIFY_SUCCESS,
                )
            )
            return response
        except Exception as exception:
            self.event_publisher.send(
                build_subscription_notify_event(
                    event_state=EventState.FAILED,
                    notify_request=request,
                    api_path=url,
                    event_name=EventType.NOTIFY_FAILED,
                    exception=exception,
                )
            )
            raise exception

    def redeem(self, merchant_order_id: str) -> SubscriptionRedeemResponseV2:
        """
        Redeem/Continue the subscription for the given ID.

        Parameters
        ----------
        merchant_order_id: str
            Same ID used at the time of making a notify request

        Returns
        ----------
        SubscriptionRedeemResponseV2:
            Contains the state for the request made
        """
        url = REDEEM_API
        headers = self.headers
        try:
            request = SubscriptionRedeemRequestV2(merchant_order_id)
            response = self._request_via_auth_refresh(
                method=HttpMethodType.POST,
                data=request.to_json(),
                url=url,
                headers=headers,
                response_obj=SubscriptionRedeemResponseV2,
            )
            self.event_publisher.send(
                build_subscription_redeem_event(
                    event_state=EventState.SUCCESS,
                    merchant_order_id=merchant_order_id,
                    api_path=url,
                    event_name=EventType.REDEEM_SUCCESS,
                )
            )
            return response
        except Exception as exception:
            self.event_publisher.send(
                build_subscription_redeem_event(
                    event_state=EventState.FAILED,
                    merchant_order_id=merchant_order_id,
                    api_path=url,
                    event_name=EventType.REDEEM_FAILED,
                    exception=exception,
                )
            )
            raise exception

    def get_subscription_status(
        self, merchant_subscription_id: str
    ) -> SubscriptionStatusResponseV2:
        """
        Gets the status of the subscription.

        Parameters
        ----------
        merchant_subscription_id: str
            Subscription ID generated by the merchant

        Returns
        ----------
        SubscriptionStatusResponseV2:
            Contains the entire status of the given subscription ID
        """
        url = SUBSCRIPTION_STATUS_API.format(
            merchant_subscription_id=merchant_subscription_id
        )
        headers = self.headers
        try:
            response = self._request_via_auth_refresh(
                method=HttpMethodType.GET,
                url=url,
                headers=headers,
                response_obj=SubscriptionStatusResponseV2,
            )
            self.event_publisher.send(
                build_subscription_event(
                    event_state=EventState.SUCCESS,
                    merchant_subscription_id=merchant_subscription_id,
                    api_path=url,
                    event_name=EventType.SUBSCRIPTION_STATUS_SUCCESS,
                )
            )
            return response
        except Exception as exception:
            self.event_publisher.send(
                build_subscription_event(
                    event_state=EventState.FAILED,
                    merchant_subscription_id=merchant_subscription_id,
                    api_path=url,
                    event_name=EventType.SUBSCRIPTION_STATUS_FAILED,
                    exception=exception,
                )
            )
            raise exception

    def get_order_status(self, merchant_order_id: str) -> OrderStatusResponse:
        """
        Gets the status of the order.

        Parameters
        ----------
        merchant_order_id: str
            Order ID generated by the merchant

        Returns
        ----------
        OrderStatusResponse:
            Contains the entire status of the given order ID
        """
        url = ORDER_STATUS_API.format(merchant_order_id=merchant_order_id)
        headers = self.headers
        try:
            response = self._request_via_auth_refresh(
                method=HttpMethodType.GET,
                url=url,
                headers=headers,
                response_obj=OrderStatusResponse,
            )
            self.event_publisher.send(
                build_order_status_event(
                    event_state=EventState.SUCCESS,
                    merchant_order_id=merchant_order_id,
                    api_path=url,
                    flow_type=FlowType.SUBSCRIPTION,
                    event_name=EventType.ORDER_STATUS_SUCCESS,
                )
            )
            return response
        except Exception as exception:
            self.event_publisher.send(
                build_order_status_event(
                    event_state=EventState.FAILED,
                    merchant_order_id=merchant_order_id,
                    api_path=url,
                    flow_type=FlowType.SUBSCRIPTION,
                    event_name=EventType.ORDER_STATUS_FAILED,
                    exception=exception,
                )
            )
            raise exception

    def get_transaction_status(self, transaction_id: str) -> OrderStatusResponse:
        """
        Gets the status of the given particular transaction ID.

        Parameters
        ----------
        transaction_id: str
            Generated by the PhonePe Side

        Returns
        ----------
        OrderStatusResponse:
            Contains the status of the particular transaction in the paymentDetails attribute
        """
        url = TRANSACTION_STATUS_API.format(transaction_id=transaction_id)
        headers = self.headers
        try:
            response = self._request_via_auth_refresh(
                method=HttpMethodType.GET,
                url=url,
                headers=headers,
                response_obj=OrderStatusResponse,
            )
            self.event_publisher.send(
                build_transaction_status_event(
                    event_state=EventState.SUCCESS,
                    transaction_id=transaction_id,
                    flow_type=FlowType.SUBSCRIPTION,
                    event_name=EventType.TRANSACTION_STATUS_SUCCESS,
                    api_path=url,
                )
            )
            return response
        except Exception as exception:
            self.event_publisher.send(
                build_transaction_status_event(
                    event_state=EventState.FAILED,
                    transaction_id=transaction_id,
                    flow_type=FlowType.SUBSCRIPTION,
                    event_name=EventType.TRANSACTION_STATUS_FAILED,
                    api_path=url,
                    exception=exception,
                )
            )
            raise exception

    def cancel_subscription(self, merchant_subscription_id) -> None:
        """
        Cancels/Stops the subscription for the given subscription ID.

        Parameters
        ----------
        merchant_subscription_id: str
            Subscription ID generated by the merchant
        """
        url = CANCEL_SUBSCRIPTION_API.format(
            merchant_subscription_id=merchant_subscription_id
        )
        headers = self.headers
        try:
            self._request_via_auth_refresh(
                method=HttpMethodType.POST, url=url, headers=headers, response_obj=None
            )
            self.event_publisher.send(
                build_subscription_event(
                    event_state=EventState.SUCCESS,
                    merchant_subscription_id=merchant_subscription_id,
                    api_path=url,
                    event_name=EventType.CANCEL_SUCCESS,
                )
            )
        except Exception as exception:
            self.event_publisher.send(
                build_subscription_event(
                    event_state=EventState.FAILED,
                    merchant_subscription_id=merchant_subscription_id,
                    api_path=url,
                    event_name=EventType.CANCEL_FAILED,
                    exception=exception,
                )
            )
            raise exception

    def refund(self, refund_request: RefundRequest) -> RefundResponse:
        """
        Initiate refund of an order.

        Parameters
        ----------
        refund_request: RefundRequest
            Request object built using RefundRequest builder

        Returns
        ----------
        RefundResponse:
            Refund details for an order
        """
        url = REFUND_API
        headers = self.headers
        try:
            response = self._request_via_auth_refresh(
                method=HttpMethodType.POST,
                url=url,
                headers=headers,
                data=refund_request.to_json(),
                response_obj=RefundResponse,
            )
            self.event_publisher.send(
                build_refund_event(
                    event_state=EventState.SUCCESS,
                    refund_request=refund_request,
                    event_name=EventType.REFUND_SUCCESS,
                    flow_type=FlowType.SUBSCRIPTION,
                    api_path=url,
                )
            )
            return response
        except Exception as exception:
            self.event_publisher.send(
                build_refund_event(
                    event_state=EventState.FAILED,
                    refund_request=refund_request,
                    event_name=EventType.REFUND_FAILED,
                    flow_type=FlowType.SUBSCRIPTION,
                    api_path=url,
                    exception=exception,
                )
            )
            raise exception

    def get_refund_status(self, merchant_refund_id: str) -> RefundStatusResponse:
        """
        Get status of the refund initiated

        Parameters
        ----------
        merchant_refund_id: str
            Merchant Refund ID for which you need the status

        Returns
        ----------
        RefundStatusResponse:
            Refund status details

        Raises
        ----------
        PhonePeException:
            If any error occurs during the process
        """
        refund_status_url = REFUND_STATUS_API.format(
            merchant_refund_id=merchant_refund_id
        )
        headers = self.headers
        try:
            response = self._request_via_auth_refresh(
                method=HttpMethodType.GET,
                url=refund_status_url,
                headers=headers,
                response_obj=RefundStatusResponse,
            )
            self.event_publisher.send(
                build_refund_status_event(
                    event_state=EventState.SUCCESS,
                    merchant_refund_id=merchant_refund_id,
                    flow_type=FlowType.SUBSCRIPTION,
                    api_path=refund_status_url,
                    event_name=EventType.REFUND_STATUS_SUCCESS,
                )
            )
            return response
        except Exception as exception:
            self.event_publisher.send(
                build_refund_status_event(
                    event_state=EventState.FAILED,
                    merchant_refund_id=merchant_refund_id,
                    flow_type=FlowType.SUBSCRIPTION,
                    api_path=refund_status_url,
                    event_name=EventType.REFUND_STATUS_FAILED,
                    exception=exception,
                )
            )
            raise exception

    def validate_callback(
        self,
        username: str,
        password: str,
        callback_header_data: str,
        callback_response_data: str,
    ) -> CallbackResponse:
        """
        Validate if the callback is valid

        Parameters
        ----------
        username: str
            username set by the merchant on the dashboard
        password: str
            password set by the merchant on the dashboard
        callback_header_data: str
            String data under `authorization` key of response headers
        callback_response_data: str
            Callback response body

        Returns
        ----------
        CallbackResponse:
            Deserialized callback body
        """
        if not is_callback_valid(
            username=username, password=password, response_header=callback_header_data
        ):
            raise PhonePeException(http_status_code=417, message="Invalid Callback")
        try:
            return CallbackResponse.from_dict(json.loads(callback_response_data))
        except Exception as exception:
            self.event_publisher.send(
                build_callback_serialization_failed_event(
                    event_state=EventState.FAILED,
                    event_name=EventType.CALLBACK_SERIALIZATION_FAILED,
                    flow_type=FlowType.SUBSCRIPTION,
                    exception=exception,
                )
            )
            raise exception
