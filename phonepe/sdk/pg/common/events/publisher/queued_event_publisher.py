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
from typing import List, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_STOPPED

from phonepe.sdk.pg.common.constants.headers import AUTHORIZATION, CONTENT_TYPE, ACCEPT, APPLICATION_JSON
from phonepe.sdk.pg.common.events.constants import EVENT_BULK_ENDPOINT, MAX_EVENTS_IN_BATCH, SEND_EVENTS_INTERVAL
from phonepe.sdk.pg.common.events.event_queue_handler import EventQueueHandler
from phonepe.sdk.pg.common.events.models.base_event import BaseEvent
from phonepe.sdk.pg.common.events.models.bulk_event import BulkEvent
from phonepe.sdk.pg.common.events.publisher.event_publisher import EventPublisher
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType


class QueuedEventPublisher(EventPublisher):
    def __init__(self, queue_handler: EventQueueHandler, event_sender: BaseHttpCommand):
        self.queue_handler: EventQueueHandler = queue_handler
        self.event_sender: BaseHttpCommand = event_sender
        self._scheduler = BackgroundScheduler()
        self.auth_token_supplier = None

    def _create_event_batches(self, max_events_in_batch):
        max_events_in_batch = max(1, max_events_in_batch)
        event_batches = []  # holds list of batches
        queue_size = self.queue_handler.cur_size()  # number of events to process (as this can change in runtime)
        cur_batch = []
        for _ in range(queue_size):
            cur_event = self.queue_handler.get()
            if cur_event is None:  # if the pointer reaches the EOF
                break
            cur_batch.append(cur_event)
            if len(cur_batch) == max_events_in_batch:
                event_batches.append(cur_batch[::])  # add current batch to list of batches
                cur_batch = []
        if len(cur_batch) != 0:  # if the last batch has some events, add to list, even if batch not full
            event_batches.append(cur_batch[::])
        return event_batches

    def _send_batch_data(self, batch: List):
        bulk_request = BulkEvent(events=batch)
        try:
            self.event_sender.request(url=EVENT_BULK_ENDPOINT, method=HttpMethodType.POST,
                                      headers={AUTHORIZATION: self.auth_token_supplier(),
                                               CONTENT_TYPE: APPLICATION_JSON,
                                               ACCEPT: APPLICATION_JSON},
                                      data=bulk_request.to_json())
        except Exception as e:
            logging.info("Error occurred sending events batch to backend", e)
        return []

    def send_events(self):
        try:
            if self.queue_handler.is_empty():
                return
            logging.info(f"Queue size {self.queue_handler.cur_size()}")
            event_batches = self._create_event_batches(MAX_EVENTS_IN_BATCH)
            self.queue_handler.delete_read_events()  # move cursor to end of current events
            for batch in event_batches:
                self._send_batch_data(batch=batch)

        except Exception as e:
            logging.error("Error occurred while sending events to backend", e)

    def send(self, event: BaseEvent):
        self.queue_handler.enqueue_event(event)

    def start_publishing_events(self, auth_token_supplier: Callable):
        self.auth_token_supplier = auth_token_supplier

        # Init a thread to call send_events_to_backend
        if self._scheduler.state == STATE_STOPPED:
            self._scheduler.start()
            logging.debug(f"Starting scheduler to send events")
            self._scheduler.add_job(self.send_events, "interval", seconds=SEND_EVENTS_INTERVAL)
