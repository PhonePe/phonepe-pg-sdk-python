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
        """Each factory instance now builds its own publisher (per-instance, not a process-wide
        singleton) - previously every client after the first silently discarded its own
        event_sender."""
        sender1 = BaseHttpCommand(host_url="")
        sender2 = BaseHttpCommand(host_url="test")
        self.addCleanup(sender1.close)
        self.addCleanup(sender2.close)

        event_publisher_factory1 = EventPublisherFactory(event_sender=sender1)
        event_publisher_factory2 = EventPublisherFactory(event_sender=sender2)

        publisher1 = event_publisher_factory1.get_event_publisher(should_publish_events=True)
        publisher2 = event_publisher_factory2.get_event_publisher(should_publish_events=True)
        self.addCleanup(publisher1.close)
        self.addCleanup(publisher2.close)

        assert publisher1 is not publisher2
        assert publisher1.event_sender is sender1
        assert publisher2.event_sender is sender2

    def test_get_event_publisher_memoizes_within_the_same_factory_instance(self):
        """Repeated calls on the SAME factory instance should still return the same publisher."""
        sender = BaseHttpCommand(host_url="")
        self.addCleanup(sender.close)
        factory = EventPublisherFactory(event_sender=sender)

        publisher1 = factory.get_event_publisher(should_publish_events=True)
        publisher2 = factory.get_event_publisher(should_publish_events=True)
        self.addCleanup(publisher1.close)

        assert publisher1 is publisher2
