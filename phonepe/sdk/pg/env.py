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

from enum import Enum

from phonepe.sdk.pg.common.constants.base_urls import PROD_PG_BASE_URL, SANDBOX_PG_BASE_URL, \
    PROD_OAUTH_BASE_URL, SANDBOX_OAUTH_BASE_URL, PROD_EVENT_INGESTION_BASE_URL, SANDBOX_EVENT_INGESTION_BASE_URL


class Env(Enum):
    PRODUCTION = "PRODUCTION"
    SANDBOX = "SANDBOX"

    def __eq__(self, other):
        return self.__class__ is other.__class__ and other.value == self.value


def get_pg_base_url(env: Env):
    if env == Env.PRODUCTION:
        return PROD_PG_BASE_URL
    return SANDBOX_PG_BASE_URL


def get_oauth_base_url(env: Env):
    if env == Env.PRODUCTION:
        return PROD_OAUTH_BASE_URL
    return SANDBOX_OAUTH_BASE_URL


def get_event_ingestion_base_url(env: Env):
    if env == Env.PRODUCTION:
        return PROD_EVENT_INGESTION_BASE_URL
    return SANDBOX_EVENT_INGESTION_BASE_URL
