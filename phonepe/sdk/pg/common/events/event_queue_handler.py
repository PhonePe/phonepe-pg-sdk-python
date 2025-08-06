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
from queue import Queue

from phonepe.sdk.pg.common.events.constants import MAX_TOTAL_EVENTS_IN_QUEUE
from phonepe.sdk.pg.common.events.models.base_event import BaseEvent


class EventQueueHandler:
    def __init__(self):
        self.queue = None
        self.initialize_queue()

    def initialize_queue(self):
        if self.queue is None:
            self.queue = Queue(maxsize=MAX_TOTAL_EVENTS_IN_QUEUE)

    def enqueue_event(self, data: BaseEvent):
        if data is None:
            return
        if self.queue.qsize() >= MAX_TOTAL_EVENTS_IN_QUEUE:
            logging.error(f"Reached queue max size, skipping ingestion of event: {data.event_name}")
            return
        try:
            self.queue.put(data, timeout=1)  # timeout prevents thread going in waiting forever
        except Exception as e:
            logging.error(e)

    def get(self):
        if self.is_empty():
            return None
        # note: pointer moves to next item for each get
        try:
            return self.queue.get(timeout=1)
        except Exception as e:
            logging.error(e)

    def delete_read_events(self):
        try:
            self.queue.task_done()
        except ValueError as e:
            pass

    def is_empty(self):
        return self.queue is None or self.queue.empty()

    def cur_size(self):
        return self.queue.qsize()

