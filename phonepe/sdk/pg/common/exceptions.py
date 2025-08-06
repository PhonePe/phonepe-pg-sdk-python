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
from json import JSONDecodeError

from requests import Response

from phonepe.sdk.pg.common.http_client_modules.phonepe_response import PhonePeResponse


class PhonePeException(Exception):

    def __init__(self, message: str, http_status_code: int = None, response: Response = None):
        self.http_status_code = http_status_code
        self.message = message
        self.code = None
        self.data = None
        if response is not None:
            try:
                response_json = response.json()
                phonepe_response_obj = PhonePeResponse.from_dict(response_json)
                self.code = phonepe_response_obj.errorCode or phonepe_response_obj.code  # keeping only the `errorCode` field for auth exception (ignoring code)
                self.data = phonepe_response_obj.context or phonepe_response_obj.data  # auth exception gives context
                self.message = phonepe_response_obj.message or self.message
            except (JSONDecodeError, AttributeError) as e:
                logging.info(f"Unable to parse response data: {response}, exception: {e}")
                raise self

    def __str__(self):
        message = f"\nHttp code: {self.http_status_code}\n"
        message += f"message: {self.message} \n"
        message += f"code: {self.code} \n"
        message += f"data: {self.data} \n"
        return message


# HTTP Request/Response related exceptions


class ClientError(PhonePeException):
    """4xx Client Error
    """
    pass


class BadRequest(ClientError):
    """400 Bad Request
    """
    pass


class UnauthorizedAccess(ClientError):
    """401 Unauthorized
    """
    pass


class ForbiddenAccess(ClientError):
    """403 Forbidden
    """
    pass


class ResourceNotFound(ClientError):
    """404 Not Found
    """
    pass


class ResourceConflict(ClientError):
    """409 Conflict
    """
    pass


class ResourceGone(ClientError):
    """410 Gone
    """
    pass


class ResourceInvalid(ClientError):
    """422 Invalid
    """
    pass


class ExpectationFailed(ClientError):
    """417 Expectation failed
    """
    pass


class TooManyRequests(ClientError):
    """429 Too Many Requests
    """
    pass


class ServerError(PhonePeException):
    """5xx Server Error
    """
    pass
