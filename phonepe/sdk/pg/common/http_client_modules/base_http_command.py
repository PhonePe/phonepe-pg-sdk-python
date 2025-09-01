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

    SESSION = Session()

    def __init__(self, host_url: str) -> None:
        self._host_url = host_url

    @staticmethod
    def get_complete_url(host_url: str, url: str):
        return f"{host_url}{url}"

    def request(self, url: str, method: HttpMethodType, headers={}, data={}, path_params={}):
        """Makes API Request"""
        complete_url = BaseHttpCommand.get_complete_url(self._host_url, url)
        logging.debug(f"Calling {method}: {complete_url}")
        if method == HttpMethodType.GET:
            return BaseHttpCommand.handle_response(
                BaseHttpCommand.SESSION.get(url=complete_url, headers=headers, params=path_params,
                                            timeout=BaseHttpCommand.TIMEOUT))
        if method == HttpMethodType.POST:
            return BaseHttpCommand.handle_response(
                BaseHttpCommand.SESSION.post(url=complete_url, headers=headers, data=data, params=path_params,
                                             timeout=BaseHttpCommand.TIMEOUT))

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
