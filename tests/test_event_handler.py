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


class TestEventPublisher(TestCase):
    def test_event_batch_maker_max_num_events_in_batch(self):
        event_sender = BaseHttpCommand(host_url="")
        queue_handler = EventQueueHandler()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)
        events_pushed = 20
        for event_id in range(events_pushed):
            queued_event_handler.send(BaseEvent(merchant_order_id=""))

        batches = queued_event_handler._create_event_batches(max_events_in_batch=100)
        assert len(batches) == max(1, events_pushed // 100)
        for batch in batches:
            assert len(batch) == min(events_pushed, 100)

    def test_event_batch_divides_equally(self):
        event_sender = BaseHttpCommand(host_url="")
        queue_handler = EventQueueHandler()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)
        events_pushed = 20
        for event_id in range(events_pushed):
            queued_event_handler.send(BaseEvent(merchant_order_id=""))

        batches = queued_event_handler._create_event_batches(max_events_in_batch=2)
        assert len(batches) == max(1, events_pushed // 2)
        for batch in batches:
            assert len(batch) == min(events_pushed, 2)

    def test_event_batch_some_left_over(self):
        event_sender = BaseHttpCommand(host_url="")
        queue_handler = EventQueueHandler()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)
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
        event_sender = BaseHttpCommand(host_url=get_event_ingestion_base_url(Env.SANDBOX))
        queue_handler = EventQueueHandler()
        cur_time = time.time_ns()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)

        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"),
                                     env=Env.PRODUCTION,
                                     event_publisher=queued_event_handler)
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
        responses.add(responses.POST, get_oauth_base_url(Env.PRODUCTION) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(token_expired_response))
        token_service.get_auth_token()
        responses.add(responses.POST, get_oauth_base_url(Env.PRODUCTION) + OAUTH_ENDPOINT, status=500)
        responses.add(responses.POST, get_oauth_base_url(Env.PRODUCTION) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(correct_token_response_data))

        event_response = responses.add(responses.POST, get_event_ingestion_base_url(Env.SANDBOX) + EVENT_BULK_ENDPOINT,
                                       status=200,
                                       headers={'Accept': 'application/json', 'Authorization': 'O-Bearer access_token',
                                                'Content-Type': 'application/json'})

        queued_event_handler.start_publishing_events(token_service.get_auth_token)
        sleep(5)
        assert event_response.call_count == 2  # first call for tokenInit events, second call for get cached token event


    @responses.activate
    def testSendsTokenFetchSuccessEvent(self):
        event_sender = BaseHttpCommand(host_url=get_event_ingestion_base_url(Env.SANDBOX))
        queue_handler = EventQueueHandler()
        queued_event_handler = QueuedEventPublisher(event_sender=event_sender,
                                                    queue_handler=queue_handler)

        token_service = TokenService(credential_config=CredentialConfig(client_id="client_id",
                                                                        client_version=1,
                                                                        client_secret="client_secret"), env=Env.SANDBOX,
                                     event_publisher=queued_event_handler)

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
        responses.add(responses.POST, get_oauth_base_url(Env.SANDBOX) + OAUTH_ENDPOINT, status=200,
                      json=json.loads(correct_token_response_data))

        event_response = responses.add(responses.POST, get_event_ingestion_base_url(Env.SANDBOX) + EVENT_BULK_ENDPOINT,
                                       status=200,
                                       headers={'Accept': 'application/json', 'Authorization': 'O-Bearer access_token',
                                                'Content-Type': 'application/json'})

        queued_event_handler.start_publishing_events(token_service.get_auth_token)
        sleep(5)

        assert event_response.call_count == 1  # only one call with init event




