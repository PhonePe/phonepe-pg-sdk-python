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

from unittest import TestCase
from unittest.mock import call, patch

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
    """Covers the generic retry-with-backoff mechanism shared by every HTTP call (GET and POST)
    made through BaseHttpCommand, regardless of which client/endpoint uses it (subscriptions,
    payments, token fetch, event ingestion, etc.)."""

    def setUp(self):
        self.command = BaseHttpCommand(host_url=BASE_URL)

    def test_max_retries_constant(self):
        # Guards against accidental changes to the configured retry budget
        assert BaseHttpCommand.MAX_RETRIES == 3

    def test_retry_backoff_delay_is_exponential(self):
        assert BaseHttpCommand._get_retry_delay(1) == 1
        assert BaseHttpCommand._get_retry_delay(2) == 2
        assert BaseHttpCommand._get_retry_delay(3) == 4

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_get_retries_on_transient_server_error_then_succeeds(self, mock_sleep):
        responses.add(responses.GET, FULL_URL, status=500)
        responses.add(responses.GET, FULL_URL, status=502)
        responses.add(responses.GET, FULL_URL, status=200, json={"ok": True})

        response = self.command.request(url=PATH, method=HttpMethodType.GET)

        assert response.json() == {"ok": True}
        assert len(responses.calls) == 3  # 2 failed retries + 1 successful attempt
        assert mock_sleep.call_args_list == [call(1), call(2)]

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_post_retries_on_transient_server_error_then_succeeds(self, mock_sleep):
        responses.add(responses.POST, FULL_URL, status=503)
        responses.add(responses.POST, FULL_URL, status=200, json={"ok": True})

        response = self.command.request(url=PATH, method=HttpMethodType.POST, data={"a": "b"})

        assert response.json() == {"ok": True}
        assert len(responses.calls) == 2  # 1 failed retry + 1 successful attempt
        assert mock_sleep.call_args_list == [call(1)]

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_retry_exhausted_raises_server_error(self, mock_sleep):
        for _ in range(BaseHttpCommand.MAX_RETRIES):
            responses.add(responses.GET, FULL_URL, status=500)

        self.assertRaises(ServerError, self.command.request, url=PATH, method=HttpMethodType.GET)

        assert len(responses.calls) == BaseHttpCommand.MAX_RETRIES  # exactly MAX_RETRIES attempts, no more
        # no sleep after the final failed attempt since we're about to give up
        assert mock_sleep.call_args_list == [call(1), call(2)]

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_retries_on_too_many_requests(self, mock_sleep):
        responses.add(responses.GET, FULL_URL, status=429)
        responses.add(responses.GET, FULL_URL, status=200, json={"ok": True})

        response = self.command.request(url=PATH, method=HttpMethodType.GET)

        assert response.json() == {"ok": True}
        assert len(responses.calls) == 2  # 1 rate-limited attempt + 1 successful retry
        assert mock_sleep.call_args_list == [call(1)]

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_too_many_requests_exhausted_raises(self, mock_sleep):
        for _ in range(BaseHttpCommand.MAX_RETRIES):
            responses.add(responses.GET, FULL_URL, status=429)

        self.assertRaises(TooManyRequests, self.command.request, url=PATH, method=HttpMethodType.GET)

        assert len(responses.calls) == BaseHttpCommand.MAX_RETRIES
        assert mock_sleep.call_args_list == [call(1), call(2)]

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_no_retry_on_bad_request(self, mock_sleep):
        # e.g. malformed payload - retrying won't fix it
        responses.add(responses.POST, FULL_URL, status=400, json={"message": "bad"})

        self.assertRaises(BadRequest, self.command.request, url=PATH, method=HttpMethodType.POST)

        assert len(responses.calls) == 1  # fails fast, no retries for a genuine client error
        mock_sleep.assert_not_called()

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_no_retry_on_unauthorized(self, mock_sleep):
        responses.add(responses.GET, FULL_URL, status=401, json={"message": "unauthorized"})

        self.assertRaises(UnauthorizedAccess, self.command.request, url=PATH, method=HttpMethodType.GET)

        assert len(responses.calls) == 1  # fails fast, no retries on 401
        mock_sleep.assert_not_called()

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_no_retry_on_not_found(self, mock_sleep):
        responses.add(responses.GET, FULL_URL, status=404, json={"message": "not found"})

        self.assertRaises(ResourceNotFound, self.command.request, url=PATH, method=HttpMethodType.GET)

        assert len(responses.calls) == 1  # fails fast, no retries on 404
        mock_sleep.assert_not_called()

    @responses.activate
    @patch("phonepe.sdk.pg.common.http_client_modules.base_http_command.sleep")
    def test_should_retry_false_disables_retries_even_on_server_error(self, mock_sleep):
        responses.add(responses.GET, FULL_URL, status=500)
        responses.add(responses.GET, FULL_URL, status=200, json={"ok": True})

        self.assertRaises(
            ServerError, self.command.request, url=PATH, method=HttpMethodType.GET, should_retry=False
        )

        assert len(responses.calls) == 1  # single attempt only, no retries
        mock_sleep.assert_not_called()

    @responses.activate
    def test_should_retry_defaults_to_true(self):
        responses.add(responses.GET, FULL_URL, status=200, json={"ok": True})

        response = self.command.request(url=PATH, method=HttpMethodType.GET)

        assert response.json() == {"ok": True}
        assert len(responses.calls) == 1
