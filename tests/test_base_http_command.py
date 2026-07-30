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

import inspect
from unittest import TestCase

import responses

from phonepe.sdk.pg.common.exceptions import (
    BadRequest,
    ResourceNotFound,
    ServerError,
    TooManyRequests,
    UnauthorizedAccess,
)
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType

BASE_URL = "https://api.phonepe.com/test"
PATH = "/ping"
FULL_URL = BASE_URL + PATH


class TestBaseHttpCommand(TestCase):
    """BaseHttpCommand makes exactly one attempt per call, for every HTTP verb and every outcome.
    The SDK does not retry requests at all: retrying is unsafe for non-idempotent calls (e.g. pay,
    refund) since the original request may already have been processed server-side even if the
    response was lost. This applies uniformly - transient server errors, rate-limiting, and client
    errors are all surfaced to the caller after a single attempt, with no built-in backoff."""

    def setUp(self):
        self.command = BaseHttpCommand(host_url=BASE_URL)

    @responses.activate
    def test_get_success_single_call(self):
        responses.add(responses.GET, FULL_URL, status=200, json={"ok": True})

        response = self.command.request(url=PATH, method=HttpMethodType.GET)

        assert response.json() == {"ok": True}
        assert len(responses.calls) == 1

    @responses.activate
    def test_post_success_single_call(self):
        responses.add(responses.POST, FULL_URL, status=200, json={"ok": True})

        response = self.command.request(url=PATH, method=HttpMethodType.POST, data={"a": "b"})

        assert response.json() == {"ok": True}
        assert len(responses.calls) == 1

    @responses.activate
    def test_no_retry_on_server_error(self):
        # Even though a subsequent attempt would have succeeded, the SDK must not retry.
        responses.add(responses.GET, FULL_URL, status=500)
        responses.add(responses.GET, FULL_URL, status=200, json={"ok": True})

        self.assertRaises(ServerError, self.command.request, url=PATH, method=HttpMethodType.GET)

        assert len(responses.calls) == 1  # exactly one attempt, no retry

    @responses.activate
    def test_no_retry_on_too_many_requests(self):
        responses.add(responses.GET, FULL_URL, status=429)
        responses.add(responses.GET, FULL_URL, status=200, json={"ok": True})

        self.assertRaises(TooManyRequests, self.command.request, url=PATH, method=HttpMethodType.GET)

        assert len(responses.calls) == 1

    @responses.activate
    def test_no_retry_on_bad_request(self):
        responses.add(responses.POST, FULL_URL, status=400, json={"message": "bad"})

        self.assertRaises(BadRequest, self.command.request, url=PATH, method=HttpMethodType.POST)

        assert len(responses.calls) == 1

    @responses.activate
    def test_no_retry_on_unauthorized(self):
        responses.add(responses.GET, FULL_URL, status=401, json={"message": "unauthorized"})

        self.assertRaises(UnauthorizedAccess, self.command.request, url=PATH, method=HttpMethodType.GET)

        assert len(responses.calls) == 1

    @responses.activate
    def test_no_retry_on_not_found(self):
        responses.add(responses.GET, FULL_URL, status=404, json={"message": "not found"})

        self.assertRaises(ResourceNotFound, self.command.request, url=PATH, method=HttpMethodType.GET)

        assert len(responses.calls) == 1

    def test_request_has_no_should_retry_parameter(self):
        # Guards against the retry flag being reintroduced on the request() signature.
        params = inspect.signature(BaseHttpCommand.request).parameters
        assert "should_retry" not in params
