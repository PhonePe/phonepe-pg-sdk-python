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
from time import sleep

from requests import Session

from phonepe.sdk.pg.common.exceptions import (BadRequest, ResourceGone, UnauthorizedAccess, ForbiddenAccess,
                                              ResourceConflict, ResourceInvalid,
                                              ResourceNotFound, ExpectationFailed, TooManyRequests)
from phonepe.sdk.pg.common.exceptions import (ClientError, ServerError,
                                              PhonePeException)
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType


class BaseHttpCommand:
    """Makes the requests to the backend"""

    HTTP_CODE_TO_EXCEPTION_MAPPER = {
        400: BadRequest,
        401: UnauthorizedAccess,
        403: ForbiddenAccess,
        404: ResourceNotFound,
        409: ResourceConflict,
        410: ResourceGone,
        417: ExpectationFailed,
        422: ResourceInvalid,
        429: TooManyRequests
    }

    TIMEOUT = 5

    MAX_RETRIES = 3
    BASE_RETRY_DELAY_SECONDS = 1  # exponential backoff: 1s, 2s, 4s, ... before each subsequent retry

    SESSION = Session()

    def __init__(self, host_url: str) -> None:
        self._host_url = host_url

    @staticmethod
    def get_complete_url(host_url: str, url: str):
        return f"{host_url}{url}"

    def request(self, url: str, method: HttpMethodType, headers={}, data={}, path_params={}, should_retry: bool = True):
        """Makes API Request.

        On transient failures (connection errors, timeouts, 5xx, 429) the request is retried up to
        MAX_RETRIES times with exponential backoff. Genuine client errors (4xx other than 429) are
        never retried. Pass should_retry=False to disable this behaviour entirely and fail fast after
        a single attempt.
        """
        complete_url = BaseHttpCommand.get_complete_url(self._host_url, url)
        logging.debug(f"Calling {method}: {complete_url}")
        if not should_retry:
            return self._send(method, complete_url, headers, data, path_params)
        return self._send_with_retries(method, complete_url, headers, data, path_params)

    def _send(self, method: HttpMethodType, complete_url: str, headers, data, path_params):
        if method == HttpMethodType.GET:
            return BaseHttpCommand.handle_response(
                BaseHttpCommand.SESSION.get(url=complete_url, headers=headers, params=path_params,
                                            timeout=BaseHttpCommand.TIMEOUT))
        if method == HttpMethodType.POST:
            return BaseHttpCommand.handle_response(
                BaseHttpCommand.SESSION.post(url=complete_url, headers=headers, data=data, params=path_params,
                                             timeout=BaseHttpCommand.TIMEOUT))

    def _send_with_retries(self, method: HttpMethodType, complete_url: str, headers, data, path_params):
        last_exception = None
        for attempt in range(1, BaseHttpCommand.MAX_RETRIES + 1):
            try:
                return self._send(method, complete_url, headers, data, path_params)
            except ClientError as exception:
                if not isinstance(exception, TooManyRequests):
                    # Genuine client-side error (bad request, unauthorized, forbidden, etc.)
                    # Retrying with the same input will fail identically, so fail fast instead.
                    logging.error(
                        f"{method} {complete_url} failed with a non-retryable client error, not retrying | "
                        f"exception_type={type(exception).__name__} | exception={exception}"
                    )
                    raise
                last_exception = exception
                logging.warning(
                    f"{method} {complete_url} attempt {attempt}/{BaseHttpCommand.MAX_RETRIES} failed with a "
                    f"rate-limit error | exception_type={type(exception).__name__} | exception={exception}"
                )
            except Exception as exception:
                last_exception = exception
                logging.warning(
                    f"{method} {complete_url} attempt {attempt}/{BaseHttpCommand.MAX_RETRIES} failed | "
                    f"exception_type={type(exception).__name__} | exception={exception} | "
                    f"cause={getattr(exception, '__cause__', None)}"
                )

            if attempt < BaseHttpCommand.MAX_RETRIES:
                delay = BaseHttpCommand._get_retry_delay(attempt)
                logging.info(
                    f"Waiting {delay}s before retrying {method} {complete_url} "
                    f"(attempt {attempt + 1}/{BaseHttpCommand.MAX_RETRIES})"
                )
                sleep(delay)

        raise last_exception

    @staticmethod
    def _get_retry_delay(attempt):
        """Exponential backoff delay (in seconds) before the given retry attempt: 1s, 2s, 4s, ..."""
        return BaseHttpCommand.BASE_RETRY_DELAY_SECONDS * (2 ** (attempt - 1))

    @staticmethod
    def handle_response(response):
        response_code = response.status_code

        if response_code in BaseHttpCommand.HTTP_CODE_TO_EXCEPTION_MAPPER:
            raise BaseHttpCommand.HTTP_CODE_TO_EXCEPTION_MAPPER[response_code](http_status_code=response.status_code,
                                                                               message=response.reason,
                                                                               response=response)
        elif 200 <= response_code <= 299:
            return response
        elif 401 <= response_code <= 499:
            raise ClientError(http_status_code=response.status_code, message=response.reason, response=response)
        elif 500 <= response_code <= 599:
            raise ServerError(http_status_code=response.status_code, message=response.reason, response=response)
        raise PhonePeException(http_status_code=response.status_code, message=response.reason, response=response)
