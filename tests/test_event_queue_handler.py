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

from phonepe.sdk.pg.common.events.event_queue_handler import EventQueueHandler
from phonepe.sdk.pg.common.events.models.base_event import BaseEvent


class TestEventQueueHandler(TestCase):

    def test_event_put(self):
        queue_handler = EventQueueHandler()

        test_data = BaseEvent(merchant_order_id="test_data")
        queue_handler.enqueue_event(test_data)
        queue_data = queue_handler.get()
        assert test_data == queue_data

