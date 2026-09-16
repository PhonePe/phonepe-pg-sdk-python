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
import time
from time import sleep
from unittest import TestCase

import responses

from phonepe.sdk.pg.common.configs.credential_config import CredentialConfig
from phonepe.sdk.pg.common.events.constants import EVENT_BULK_ENDPOINT
from phonepe.sdk.pg.common.events.event_queue_handler import EventQueueHandler
from phonepe.sdk.pg.common.events.models.base_event import BaseEvent
from phonepe.sdk.pg.common.events.publisher.queued_event_publisher import QueuedEventPublisher
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand
from phonepe.sdk.pg.common.token_handler.token_constants import OAUTH_ENDPOINT
from phonepe.sdk.pg.common.token_handler.token_service import TokenService
from phonepe.sdk.pg.env import Env, get_oauth_base_url, get_event_ingestion_base_url
from phonepe.sdk.pg.common.configs.http_client_config import HttpClientConfig


class TestEventPublisher(TestCase):
    def test_event_batch_maker_max_num_events_in_batch(self):
        event_sender = BaseHttpCommand(host_url="", http_client_config=HttpClientConfig())
        self.addCleanup(event_sender.close)
        queue_handler = EventQueueHandler()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)
        self.addCleanup(queued_event_handler.close)
        events_pushed = 20
        for event_id in range(events_pushed):
            queued_event_handler.send(BaseEvent(merchant_order_id=""))

        batches = queued_event_handler._create_event_batches(max_events_in_batch=100)
        assert len(batches) == max(1, events_pushed // 100)
        for batch in batches:
            assert len(batch) == min(events_pushed, 100)

    def test_event_batch_divides_equally(self):
        event_sender = BaseHttpCommand(host_url="", http_client_config=HttpClientConfig())
        self.addCleanup(event_sender.close)
        queue_handler = EventQueueHandler()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)
        self.addCleanup(queued_event_handler.close)
        events_pushed = 20
        for event_id in range(events_pushed):
            queued_event_handler.send(BaseEvent(merchant_order_id=""))

        batches = queued_event_handler._create_event_batches(max_events_in_batch=2)
        assert len(batches) == max(1, events_pushed // 2)
        for batch in batches:
            assert len(batch) == min(events_pushed, 2)

    def test_event_batch_some_left_over(self):
        event_sender = BaseHttpCommand(host_url="", http_client_config=HttpClientConfig())
        self.addCleanup(event_sender.close)
        queue_handler = EventQueueHandler()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)
        self.addCleanup(queued_event_handler.close)
        max_events_in_batch = 5
        split_over_events = 3
        events_pushed = 4 * max_events_in_batch + split_over_events
        for event_id in range(events_pushed):
            queued_event_handler.send(BaseEvent(merchant_order_id=""))

        batches = queued_event_handler._create_event_batches(max_events_in_batch=max_events_in_batch)
        assert len(batches) == max(1, (events_pushed // max_events_in_batch) +
                                   max(1, split_over_events // max_events_in_batch))
        for batch in batches[:-1]:
            assert len(batch) == min(events_pushed, 5)
        assert len(batches[-1]) == split_over_events

    @responses.activate
    def testSendsTokenFetchFailureEvent(self):
        event_sender = BaseHttpCommand(host_url=get_event_ingestion_base_url(Env.SANDBOX), http_client_config=HttpClientConfig())
        self.addCleanup(event_sender.close)
        queue_handler = EventQueueHandler()
        cur_time = time.time_ns()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)
        self.addCleanup(queued_event_handler.close)

        token_expired_response = """{
                                                    "access_token": "access_token",
                                                    "encrypted_access_token": "encrypted_access_token",
                                                    "refresh_token": "refresh_token",
                                                    "expires_in": 0,
                                                    "issued_at": 0,
                                                    "expires_at": 0,
                                                    "session_expires_at": 1709630316,
                                                    "token_type": "O-Bearer"
                                                    }
                                                """
        # Registered before construction: TokenService now eagerly fetches its token at
        # construction time (rather than lazily on the first get_auth_token() call).
        responses.add(responses.POST, get_oauth_base_url(Env.PRODUCTION) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_expired_response))
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"),
                                     env=Env.PRODUCTION,
                                     event_publisher=queued_event_handler, http_client_config=HttpClientConfig())
        self.addCleanup(token_service.close)
        token_service.start()

        cur_time = int(time.time_ns())  # Example value for cur_time
        two_sec_more_cur = int(cur_time + 200)

        correct_token_response_data = f"""{{
                    "access_token": "access_token",
                    "encrypted_access_token": "encrypted_access_token",
                    "refresh_token": "refresh_token",
                    "expires_in": 200,
                    "issued_at": {cur_time},
                    "expires_at": {two_sec_more_cur},
                    "session_expires_at": 1709630316,
                    "token_type": "O-Bearer"
                }}
                """
        # Do NOT call get_auth_token() here: the eager fetch during construction already cached
        # the (immediately invalid, expires_in=0) token. This 500 is intentionally left for the
        # scheduler's first send_events() tick to hit when it calls auth_token_supplier() to get
        # a header for sending the already-queued init event - which publishes the "used cached
        # token, refresh failed" event as a side effect, matching this test's expectation of two
        # separate ticks (and thus two separate event_response calls).
        responses.add(responses.POST, get_oauth_base_url(Env.PRODUCTION) + OAUTH_ENDPOINT, status=500)
        responses.add(responses.POST, get_oauth_base_url(Env.PRODUCTION) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(correct_token_response_data))

        event_response = responses.add(responses.POST, get_event_ingestion_base_url(Env.SANDBOX) + EVENT_BULK_ENDPOINT,
                                       status=200,
                                       headers={'Accept': 'application/json', 'Authorization': 'O-Bearer access_token',
                                                'Content-Type': 'application/json'})

        queued_event_handler.start_publishing_events(token_service.get_auth_token)
        sleep(5)
        # The proactive background refresh thread and the scheduler's own send_events() tick
        # (which needs a fresh auth header via auth_token_supplier() to send the queued init
        # event) now race to be the one that discovers/refreshes the invalid token, so the exact
        # number of separate event-batch HTTP calls is no longer deterministic (it was tied to
        # old lazy-fetch-only timing). What matters is that both the init event and the refresh-
        # failure event actually got delivered - check that across all delivered batches instead
        # of pinning an exact call count.
        assert event_response.call_count >= 1
        delivered_bodies = "".join(
            call.request.body.decode() if isinstance(call.request.body, bytes) else str(call.request.body)
            for call in responses.calls if call.request.url == event_response.url
        )
        assert "TOKEN_SERVICE_INITIALIZED" in delivered_bodies
        assert "OAUTH_FETCH_FAILED_USED_CACHED_TOKEN" in delivered_bodies


    @responses.activate
    def testSendsTokenFetchSuccessEvent(self):
        event_sender = BaseHttpCommand(host_url=get_event_ingestion_base_url(Env.SANDBOX), http_client_config=HttpClientConfig())
        self.addCleanup(event_sender.close)
        queue_handler = EventQueueHandler()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)
        self.addCleanup(queued_event_handler.close)

        cur_time = int(time.time_ns())  # Example value for cur_time
        two_sec_more_cur = int(cur_time + 200)

        correct_token_response_data = f"""{{
                    "access_token": "access_token",
                    "encrypted_access_token": "encrypted_access_token",
                    "refresh_token": "refresh_token",
                    "expires_in": 200,
                    "issued_at": {cur_time},
                    "expires_at": {two_sec_more_cur},
                    "session_expires_at": 1709630316,
                    "token_type": "O-Bearer"
                }}
                """
        # Registered before construction: TokenService now eagerly fetches its token at
        # construction time (rather than lazily on the first get_auth_token() call).
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(correct_token_response_data))
        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=queued_event_handler, http_client_config=HttpClientConfig())
        self.addCleanup(token_service.close)
        token_service.start()

        event_response = responses.add(responses.POST, get_event_ingestion_base_url(Env.SANDBOX) + EVENT_BULK_ENDPOINT,
                                       status=200,
                                       headers={'Accept': 'application/json', 'Authorization': 'O-Bearer access_token',
                                                'Content-Type': 'application/json'})

        queued_event_handler.start_publishing_events(token_service.get_auth_token)
        sleep(5)

        assert event_response.call_count == 1  # only one call with init event




