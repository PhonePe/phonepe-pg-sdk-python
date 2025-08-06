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
from typing import Dict

from phonepe.sdk.pg.common.base_client import BaseClient
from phonepe.sdk.pg.common.events.event_builder import build_init_client_event, build_order_status_event, \
    build_refund_event, build_standard_checkout_pay_event, build_create_sdk_order_event, build_transaction_status_event, \
    build_refund_status_event, build_callback_serialization_failed_event
from phonepe.sdk.pg.common.events.models.enums.event_state import EventState
from phonepe.sdk.pg.common.events.models.enums.event_type import EventType
from phonepe.sdk.pg.common.events.models.enums.flow_type import FlowType
from phonepe.sdk.pg.common.exceptions import PhonePeException
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType
from phonepe.sdk.pg.common.utils.hash_utils import is_callback_valid, calculate_hash
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v2.models.request.create_sdk_order_request import CreateSdkOrderRequest
from phonepe.sdk.pg.common.models.request.refund_request import RefundRequest
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from phonepe.sdk.pg.payments.v2.models.callback_response import CallbackResponse
from phonepe.sdk.pg.payments.v2.models.response.create_sdk_order_response import \
    CreateSdkOrderResponse
from phonepe.sdk.pg.common.models.response.order_status_response import OrderStatusResponse
from phonepe.sdk.pg.common.models.response.refund_response import RefundResponse
from phonepe.sdk.pg.common.models.response.refund_status_response import RefundStatusResponse
from phonepe.sdk.pg.payments.v2.models.response.standard_checkout_pay_response import StandardCheckoutPayResponse
from phonepe.sdk.pg.payments.v2.standard_checkout.standard_checkout_constants import REFUND_STATUS_API, \
    ORDER_STATUS_API, PAY_API, REFUND_API, \
    TRANSACTION_STATUS_API, CREATE_ORDER_API, ORDER_DETAILS


class StandardCheckoutClient(BaseClient):
    """
    The StandardCheckout client class provides methods for interacting with the PhonePe APIs.
    """
    _cached_instances: Dict[str, BaseClient] = {}

    def __init__(self, client_id: str, client_version: int, client_secret: str, env: Env,
                 should_publish_events: bool = True):
        should_publish_events = should_publish_events and env == Env.PRODUCTION
        super().__init__(client_id, client_secret, client_version, env, should_publish_events)

    @staticmethod
    def get_instance(client_id: str, client_secret: str, client_version: int, env: Env = Env.SANDBOX,
                     should_publish_events: bool = True):
        """
        Init StandardCheckoutClient class with merchant-credentials

        Parameters
        ----------
        client_id: str
            Unique client-id assigned to merchant by PhonePe
        client_version:
            The client version used for secure transactions
        client_secret: str
            Secret provided by PhonePe
        env: Env
            Set to `Env.SANDBOX` for the sandbox environment  or `Env.PRODUCTION` for the production environment.
            The default value is `Env.SANDBOX`
        should_publish_events: bool
            When true events are sent to PhonePe providing smoother experience
        """
        should_publish_events = should_publish_events and env == Env.PRODUCTION
        requested_client_sha = calculate_hash(str(client_id), str(client_version), str(client_secret), str(env),
                                              str(should_publish_events), str(FlowType.PG_CHECKOUT))
        if requested_client_sha in StandardCheckoutClient._cached_instances.keys():
            return StandardCheckoutClient._cached_instances[requested_client_sha]

        new_instance = StandardCheckoutClient(client_id=client_id,
                                              client_version=client_version,
                                              client_secret=client_secret,
                                              env=env,
                                              should_publish_events=should_publish_events)
        StandardCheckoutClient._cached_instances[requested_client_sha] = new_instance
        init_event = build_init_client_event(flow_type=FlowType.PG_CHECKOUT,
                                             event_name=EventType.STANDARD_CHECKOUT_CLIENT_INITIALIZED)
        new_instance.event_publisher.send(init_event)
        return StandardCheckoutClient._cached_instances[requested_client_sha]

    def pay(self, pay_request: StandardCheckoutPayRequest) -> StandardCheckoutPayResponse:
        """
        Initiate pay order

        Parameters
        ----------
        pay_request: StandardCheckoutPayRequest
            Request object build using StandardCheckoutPayRequest builder

        Returns
        ----------
        StandardCheckoutPayResponse:
            contains checkout page url and related details
        """
        try:
            response = self._request_via_auth_refresh(method=HttpMethodType.POST,
                                                      url=PAY_API,
                                                      data=pay_request.to_json(),
                                                      response_obj=StandardCheckoutPayResponse)
            self.event_publisher.send(build_standard_checkout_pay_event(event_state=EventState.SUCCESS,
                                                                        standard_checkout_pay_request=pay_request,
                                                                        api_path=PAY_API,
                                                                        event_name=EventType.PAY_SUCCESS))
            return response
        except Exception as exception:
            self.event_publisher.send(build_standard_checkout_pay_event(event_state=EventState.FAILED,
                                                                        standard_checkout_pay_request=pay_request,
                                                                        api_path=PAY_API,
                                                                        event_name=EventType.PAY_FAILED,
                                                                        exception=exception))
            raise exception

    def get_order_status(self, merchant_order_id: str, details: bool = False) -> OrderStatusResponse:
        """
        Get status of an order

        Parameters
        ----------
        merchant_order_id: str
            Order id generated by merchant
        details: bool
            When details=True, order status has all attempt details under paymentDetails list (default=False)
            When details=False, order status has only latest attempt details under paymentDetails list

        Returns
        ----------
        OrderStatusResponse:
            Response with order and transaction details
        """
        order_status_url = ORDER_STATUS_API.format(merchant_order_id=merchant_order_id)
        try:
            response = self._request_via_auth_refresh(method=HttpMethodType.GET,
                                                      url=order_status_url,
                                                      path_params={ORDER_DETAILS: details},
                                                      response_obj=OrderStatusResponse)
            self.event_publisher.send(build_order_status_event(event_state=EventState.SUCCESS,
                                                               merchant_order_id=merchant_order_id,
                                                               api_path=order_status_url,
                                                               flow_type=FlowType.PG_CHECKOUT,
                                                               event_name=EventType.ORDER_STATUS_SUCCESS))
            return response
        except Exception as exception:
            self.event_publisher.send(build_order_status_event(event_state=EventState.FAILED,
                                                               merchant_order_id=merchant_order_id,
                                                               api_path=order_status_url,
                                                               flow_type=FlowType.PG_CHECKOUT,
                                                               event_name=EventType.ORDER_STATUS_FAILED,
                                                               exception=exception))
            raise exception

    def validate_callback(self, username: str, password: str, callback_header_data: str,
                          callback_response_data: str) -> CallbackResponse:
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
        if not is_callback_valid(username=username, password=password, response_header=callback_header_data):
            raise PhonePeException(http_status_code=417, message="Invalid Callback")

        try:
            return CallbackResponse.from_dict(json.loads(callback_response_data))
        except Exception as exception:
            self.event_publisher.send(
                build_callback_serialization_failed_event(event_state=EventState.FAILED,
                                                          event_name=EventType.CALLBACK_SERIALIZATION_FAILED,
                                                          flow_type=FlowType.PG_CHECKOUT,
                                                          exception=exception))
            raise exception

    def get_refund_status(self, merchant_refund_id: str) -> RefundStatusResponse:
        """
        Get status of refund

        Parameters
        ----------
        merchant_refund_id:
            Merchant Refund id for which you need the status

        Returns
        ----------
        RefundStatusResponse:
            Refund status details
        """
        refund_status_url = REFUND_STATUS_API.format(merchant_refund_id=merchant_refund_id)
        try:
            response = self._request_via_auth_refresh(method=HttpMethodType.GET,
                                                      url=refund_status_url,
                                                      response_obj=RefundStatusResponse)
            self.event_publisher.send(build_refund_status_event(event_state=EventState.SUCCESS,
                                                                merchant_refund_id=merchant_refund_id,
                                                                flow_type=FlowType.PG_CHECKOUT,
                                                                api_path=refund_status_url,
                                                                event_name=EventType.REFUND_STATUS_SUCCESS))
            return response
        except Exception as exception:
            self.event_publisher.send(build_refund_status_event(event_state=EventState.FAILED,
                                                                merchant_refund_id=merchant_refund_id,
                                                                flow_type=FlowType.PG_CHECKOUT,
                                                                api_path=refund_status_url,
                                                                event_name=EventType.REFUND_STATUS_FAILED,
                                                                exception=exception))
            raise exception

    def get_transaction_status(self, transaction_id: str) -> OrderStatusResponse:
        """
        Get status of a transaction attempt

        Parameters
        ----------
        transaction_id:
            Transaction attempt id generated by PhonePe

        Returns
        ----------
        OrderStatusResponse:
            Response with order and transaction details
        """
        transaction_status_url = TRANSACTION_STATUS_API.format(transaction_id=transaction_id)
        try:
            response = self._request_via_auth_refresh(method=HttpMethodType.GET,
                                                      url=transaction_status_url,
                                                      response_obj=OrderStatusResponse)
            self.event_publisher.send(build_transaction_status_event(event_state=EventState.SUCCESS,
                                                                     transaction_id=transaction_id,
                                                                     flow_type=FlowType.PG_CHECKOUT,
                                                                     api_path=transaction_status_url,
                                                                     event_name=EventType.TRANSACTION_STATUS_SUCCESS))
            return response
        except Exception as exception:
            self.event_publisher.send(build_transaction_status_event(event_state=EventState.FAILED,
                                                                     transaction_id=transaction_id,
                                                                     flow_type=FlowType.PG_CHECKOUT,
                                                                     api_path=transaction_status_url,
                                                                     event_name=EventType.TRANSACTION_STATUS_FAILED,
                                                                     exception=exception))
            raise exception

    def refund(self, refund_request: RefundRequest) -> RefundResponse:
        """
        Initiate refund of an order

        Parameters
        ----------
        refund_request:
            Request object build using RefundRequest builder

        Returns
        ----------
        RefundResponse:
            contains refund details for an order
        """
        try:
            response = self._request_via_auth_refresh(method=HttpMethodType.POST,
                                                      url=REFUND_API,
                                                      data=refund_request.to_json(),
                                                      response_obj=RefundResponse)
            self.event_publisher.send(build_refund_event(event_state=EventState.SUCCESS,
                                                         refund_request=refund_request,
                                                         flow_type=FlowType.PG_CHECKOUT,
                                                         api_path=REFUND_API,
                                                         event_name=EventType.REFUND_SUCCESS))
            return response
        except Exception as exception:
            self.event_publisher.send(build_refund_event(event_state=EventState.FAILED,
                                                         refund_request=refund_request,
                                                         flow_type=FlowType.PG_CHECKOUT,
                                                         api_path=REFUND_API,
                                                         event_name=EventType.REFUND_FAILED,
                                                         exception=exception))
            raise exception

    def create_sdk_order(self, sdk_order_request: CreateSdkOrderRequest) -> CreateSdkOrderResponse:
        """
        Create order token for SDK integrated order requests

        Parameters
        ----------
        sdk_order_request:
            Request object build using CreateSdkOrderRequest builder

        Returns
        ----------
        CreateSdkOrderResponse:
            contains token details to be consumed by the UI
        """
        try:
            response = self._request_via_auth_refresh(method=HttpMethodType.POST,
                                                      url=CREATE_ORDER_API,
                                                      data=sdk_order_request.to_json(),
                                                      response_obj=CreateSdkOrderResponse)
            self.event_publisher.send(build_create_sdk_order_event(event_state=EventState.SUCCESS,
                                                                   create_sdk_order_request=sdk_order_request,
                                                                   api_path=CREATE_ORDER_API,
                                                                   flow_type=FlowType.PG_CHECKOUT,
                                                                   event_name=EventType.CREATE_SDK_ORDER_SUCCESS))
            return response
        except Exception as exception:
            self.event_publisher.send(build_create_sdk_order_event(event_state=EventState.FAILED,
                                                                   create_sdk_order_request=sdk_order_request,
                                                                   api_path=CREATE_ORDER_API,
                                                                   flow_type=FlowType.PG_CHECKOUT,
                                                                   event_name=EventType.CREATE_SDK_ORDER_FAILED,
                                                                   exception=exception))
            raise exception
