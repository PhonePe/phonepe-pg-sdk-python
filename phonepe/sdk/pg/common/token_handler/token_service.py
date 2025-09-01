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

import logging
from time import time

from phonepe.sdk.pg.common.configs.credential_config import CredentialConfig
from phonepe.sdk.pg.common.constants.headers import (
    ACCEPT,
    CONTENT_TYPE,
    APPLICATION_JSON,
    X_WWW_FORM_URLENCODED,
)
from phonepe.sdk.pg.common.events.event_builder import (
    build_init_client_event,
    build_oauth_event_used_cached_token_failed,
)
from phonepe.sdk.pg.common.events.models.enums.event_type import EventType
from phonepe.sdk.pg.common.events.publisher.event_publisher import EventPublisher
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType
from phonepe.sdk.pg.common.token_handler.oauth_response import OauthResponse
from phonepe.sdk.pg.common.token_handler.token_constants import (
    OAUTH_GRANT_TYPE,
    OAUTH_ENDPOINT,
)
from phonepe.sdk.pg.env import Env, get_oauth_base_url


class TokenService:
    """Token management"""


    def __init__(
        self,
        credential_config: CredentialConfig,
        env: Env,
        event_publisher: EventPublisher,
    ) -> None:
        self._credential_config = credential_config
        self._http_command = BaseHttpCommand(host_url=get_oauth_base_url(env))
        self.event_publisher = event_publisher
        self.event_publisher.send(
            build_init_client_event(event_name=EventType.TOKEN_SERVICE_INITIALIZED)
        )
        self.cached_token_data = None

    def get_current_time(self):
        return int(time())

    def _is_cached_token_valid(self):
        """Checks if token has expired"""
        if self.cached_token_data is None:
            return False

        issued_at = self.cached_token_data.issued_at
        expires_at = self.cached_token_data.expires_at
        current_time = self.get_current_time()

        token_sdk_expiry_time = issued_at + int((expires_at - issued_at) // 2)
        return current_time < token_sdk_expiry_time

    def get_auth_token(self):
        if self._is_cached_token_valid():
            return (
                self.cached_token_data.token_type
                + " "
                + self.cached_token_data.access_token
            )
        try:
            token_data = self.fetch_token_from_phonepe().json()
            self.cached_token_data = OauthResponse.from_dict(token_data)
        except Exception as exception:
            if self.cached_token_data is None:
                logging.error(
                    f"No cached token, error occurred while fetching new token {exception}"
                )
                raise exception
            self.event_publisher.send(
                build_oauth_event_used_cached_token_failed(
                    cached_token_issued_at=self.cached_token_data.issued_at,
                    cached_token_expires_at=self.cached_token_data.expires_at,
                    fetch_attempt_time=self.get_current_time(),
                    api_path=OAUTH_ENDPOINT,
                    exception=exception,
                )
            )
            logging.info(
                f"Returning cached token, error occurred while fetching new token {exception}"
            )

        # always return cached token, even if auth-client throws exception
        return (
            self.cached_token_data.token_type
            + " "
            + self.cached_token_data.access_token
        )

    def force_refresh_token(self):
        logging.info("Force refreshing token")
        token_data = self.fetch_token_from_phonepe().json()
        self.cached_token_data = OauthResponse.from_dict(token_data)

    def fetch_token_from_phonepe(self):
        return self._http_command.request(
            method=HttpMethodType.POST,
            url=OAUTH_ENDPOINT,
            data=self._prepare_oauth_body(),
            headers=self._prepare_oauth_headers(),
        )

    def _prepare_oauth_headers(self):
        return {CONTENT_TYPE: X_WWW_FORM_URLENCODED, ACCEPT: APPLICATION_JSON}

    def _prepare_oauth_body(self):
        return {
            "client_id": self._credential_config.client_id,
            "client_secret": self._credential_config.client_secret,
            "grant_type": OAUTH_GRANT_TYPE,
            "client_version": self._credential_config.client_version,
        }
