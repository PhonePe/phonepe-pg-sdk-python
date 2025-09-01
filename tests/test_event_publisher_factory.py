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

from phonepe.sdk.pg.common.events.publisher.event_publisher_factory import EventPublisherFactory
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand


class TestEventPublisherFactory(TestCase):

    def test_get_event_publisher(self):
        event_publisher_factory1 = EventPublisherFactory(event_sender=
                                                         BaseHttpCommand(host_url=""))
        event_publisher_factory2 = EventPublisherFactory(event_sender=
                                                         BaseHttpCommand(host_url="test"))

        publisher1 = event_publisher_factory1.get_event_publisher(should_publish_events=True)
        publisher2 = event_publisher_factory2.get_event_publisher(should_publish_events=True)
        assert publisher1 == publisher2
