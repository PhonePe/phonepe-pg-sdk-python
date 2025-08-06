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

from phonepe.sdk.pg.common.events.event_queue_handler import EventQueueHandler
from phonepe.sdk.pg.common.events.publisher.event_publisher import EventPublisher
from phonepe.sdk.pg.common.events.publisher.queued_event_publisher import QueuedEventPublisher
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand


class EventPublisherFactory:
    cached_publisher = None

    def __init__(self, event_sender: BaseHttpCommand):
        self.event_sender = event_sender

    def get_event_publisher(self, should_publish_events: bool):
        if should_publish_events:
            if not EventPublisherFactory.cached_publisher:
                EventPublisherFactory.cached_publisher = QueuedEventPublisher(queue_handler=EventQueueHandler(),
                                                                              event_sender=self.event_sender)
            return EventPublisherFactory.cached_publisher
        return EventPublisher()
