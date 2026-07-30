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

import time
from functools import partial

from requests.adapters import DEFAULT_POOLBLOCK, HTTPAdapter
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool


class _RecyclingPoolMixin:
    """Mixed into urllib3's HTTPConnectionPool/HTTPSConnectionPool to proactively enforce a
    keep-alive limit on pooled connections.

    Background: repro testing (see repro_stale_connection.py) showed that PhonePe's
    server/load-balancer silently closes idle connections after a few hundred seconds. Since
    the SDK no longer retries requests (retrying is unsafe for non-idempotent calls like pay/
    refund), a connection that goes stale while sitting in the pool must never be handed to a
    request in the first place - there would be no second attempt to fall back on.

    This overrides `_get_conn` (the single choke point where urllib3 either returns a pooled
    connection or mints a new one) to track how long each connection object has been alive and
    proactively `.close()` any reused connection whose age exceeds `keep_alive_seconds` *before*
    handing it back. Closing sets the connection's `.sock` back to `None`, so urllib3's own
    `HTTPConnection.request()` logic (`if self.sock is None: self.connect()`) transparently
    establishes a fresh socket on the very next use - reusing urllib3's existing reconnect path
    instead of duplicating it.

    Tracking state (`_conn_opened_at`) is a plain instance attribute, scoped to this one pool
    instance - never global/class-level - so it cannot affect any other connection pool
    elsewhere in the same process.
    """

    def __init__(self, *args, keep_alive_seconds=60, **kwargs):
        super().__init__(*args, **kwargs)
        self._keep_alive_seconds = keep_alive_seconds
        self._conn_opened_at = {}  # id(conn) -> time.time() this connection was (re)established

    def _get_conn(self, timeout=None):
        conn = super()._get_conn(timeout=timeout)
        now = time.time()
        is_new = getattr(conn, "sock", None) is None
        if is_new:
            # Brand new connection object - not yet connected. The actual connect() happens
            # synchronously right after this, within the same request call chain, so recording
            # the checkout time here is accurate enough (within milliseconds) without needing
            # to patch HTTPConnection.connect() itself.
            self._conn_opened_at[id(conn)] = now
            return conn

        opened_at = self._conn_opened_at.get(id(conn))
        if opened_at is not None and (now - opened_at) > self._keep_alive_seconds:
            conn.close()
            # About to be transparently reconnected on next use; reset the tracked age so it
            # isn't immediately considered stale again.
            self._conn_opened_at[id(conn)] = now
        return conn


class RecyclingHTTPConnectionPool(_RecyclingPoolMixin, HTTPConnectionPool):
    pass


class RecyclingHTTPSConnectionPool(_RecyclingPoolMixin, HTTPSConnectionPool):
    pass


class RecyclingHTTPAdapter(HTTPAdapter):
    """A requests HTTPAdapter that proactively recycles pooled connections older than
    `keep_alive_seconds`, on top of the usual pool_connections/pool_maxsize sizing.

    The pool-class override below is applied to this adapter's own `PoolManager` instance only
    (`pool_classes_by_scheme` is set fresh per-PoolManager in urllib3, never shared class/global
    state), so multiple BaseHttpCommand instances - potentially with different HttpClientConfig
    settings - can safely coexist in the same merchant process without interfering with each
    other or with any other library's use of requests/urllib3 in that process.
    """

    def __init__(self, *args, keep_alive_seconds=60, **kwargs):
        self._keep_alive_seconds = keep_alive_seconds
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)
        self.poolmanager.pool_classes_by_scheme = {
            "http": partial(RecyclingHTTPConnectionPool, keep_alive_seconds=self._keep_alive_seconds),
            "https": partial(RecyclingHTTPSConnectionPool, keep_alive_seconds=self._keep_alive_seconds),
        }
