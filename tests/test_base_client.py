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

import threading
import time
from unittest import TestCase

import responses

from phonepe.sdk.pg.common.base_client import BaseClient
from phonepe.sdk.pg.common.exceptions import PhonePeException
from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.env import Env, get_oauth_base_url


def _bad_credentials_oauth_mock():
    responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=400,
                  json={"code": "INVALID_CLIENT", "errorCode": "OIM000",
                        "message": "Bad Request: Invalid Client, trackingId: 2123d",
                        "context": {"error_description": "Client authentication failure"}})


def _new_threads_still_alive_after(before_names, settle_seconds=0.5):
    """Returns thread names newly alive that weren't before (after a brief settle delay)."""
    time.sleep(settle_seconds)
    after_names = set(t.name for t in threading.enumerate())
    return after_names - before_names


class TestBaseClientConstructionCleanup(TestCase):
    """Regression coverage: if BaseClient.__init__ fails partway (e.g. TokenService's eager
    fetch raising fast on bad credentials), every thread already started by an earlier step
    must be cleaned up - not leaked forever."""

    @responses.activate
    def test_no_thread_leak_when_construction_fails_fast_events_disabled(self):
        _bad_credentials_oauth_mock()
        before = set(t.name for t in threading.enumerate())

        self.assertRaises(PhonePeException, BaseClient,
                          client_id="client_id", client_secret="client_secret", client_version=1,
                          env=Env.SANDBOX, should_publish_events=False)

        leaked = _new_threads_still_alive_after(before)
        assert not leaked, f"threads leaked after failed construction: {leaked}"

    @responses.activate
    def test_no_thread_leak_when_construction_fails_fast_events_enabled(self):
        # should_publish_events=True also exercises the event-ingestion/QueuedEventPublisher path.
        _bad_credentials_oauth_mock()
        before = set(t.name for t in threading.enumerate())

        self.assertRaises(PhonePeException, BaseClient,
                          client_id="client_id", client_secret="client_secret", client_version=1,
                          env=Env.SANDBOX, should_publish_events=True)

        leaked = _new_threads_still_alive_after(before)
        assert not leaked, f"threads leaked after failed construction: {leaked}"

    @responses.activate
    def test_successful_construction_close_stops_all_threads(self):
        # Sanity companion: a successful construction's threads must be stoppable via close().
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json={"access_token": "access_token", "encrypted_access_token": "enc",
                            "refresh_token": "refresh_token", "expires_in": 5014,
                            "issued_at": int(time.time()), "expires_at": int(time.time()) + 5014,
                            "session_expires_at": int(time.time()) + 5014, "token_type": "O-Bearer"})
        before = set(t.name for t in threading.enumerate())

        client = BaseClient(client_id="client_id", client_secret="client_secret", client_version=1,
                            env=Env.SANDBOX, should_publish_events=True)
        client.close()

        leaked = _new_threads_still_alive_after(before)
        assert not leaked, f"threads leaked after close() on a successfully constructed client: {leaked}"
