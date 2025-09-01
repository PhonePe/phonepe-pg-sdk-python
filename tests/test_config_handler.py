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
from unittest.mock import patch

from phonepe.sdk.pg.env import Env, get_pg_base_url, get_oauth_base_url


class TestConfigHandler(TestCase):

    @patch("phonepe.sdk.pg.env.PROD_PG_BASE_URL", "pg_prod_base_url")
    def test_get_phonepe_url_prod_host(self):
        url = get_pg_base_url(Env.PRODUCTION)
        assert url == "pg_prod_base_url"

    @patch("phonepe.sdk.pg.env.SANDBOX_PG_BASE_URL", "pg_uat_base_url")
    def test_get_phonepe_url_uat_host(self):
        url = get_pg_base_url(Env.SANDBOX)
        assert url == "pg_uat_base_url"

    @patch("phonepe.sdk.pg.env.PROD_OAUTH_BASE_URL", "oauth_prod_url")
    def test_get_oauth_url_prod_host(self):
        url = get_oauth_base_url(Env.PRODUCTION)
        assert url == "oauth_prod_url"

    @patch("phonepe.sdk.pg.env.SANDBOX_OAUTH_BASE_URL", "oauth_uat_url")
    def test_get_oauth_url_uat_host(self):
        url = get_oauth_base_url(Env.SANDBOX)
        assert url == "oauth_uat_url"
