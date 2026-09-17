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

import http.server
import socketserver
import threading
import time
from unittest import TestCase

import requests

from phonepe.sdk.pg.common.configs.http_client_config import HttpClientConfig
from phonepe.sdk.pg.common.http_client_modules.base_http_command import BaseHttpCommand
from phonepe.sdk.pg.common.http_client_modules.http_method_type import HttpMethodType
from phonepe.sdk.pg.common.http_client_modules.recycling_http_adapter import RecyclingHTTPAdapter


class _SlowHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        # Slow enough that a concurrent burst genuinely overlaps and contends for the pool.
        time.sleep(0.5)
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class _Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # keep-alive support, required to actually pool connections

    def do_GET(self):
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # silence per-request logging


class _ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


class TestRecyclingHTTPAdapter(TestCase):
    """RecyclingHTTPAdapter enforces keep_alive_seconds two ways: lazily (a connection is
    checked for staleness the next time a request actually reuses it) and proactively (a
    background sweep thread periodically closes idle connections directly, regardless of
    request activity). These tests use a real local HTTP/1.1 server since the behavior being
    tested is genuine socket-level connection reuse/closure, not mockable at the `requests`
    layer."""

    def setUp(self):
        self.server = _ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self.server.server_address[1]
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.addCleanup(self.server.shutdown)

        self.session = requests.Session()
        self.addCleanup(self.session.close)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/"

    def _mount_adapter(self, keep_alive_seconds):
        adapter = RecyclingHTTPAdapter(pool_connections=5, pool_maxsize=5,
                                       keep_alive_seconds=keep_alive_seconds)
        self.session.mount("http://", adapter)
        self.addCleanup(adapter.close)
        return adapter

    def test_connection_reused_within_keep_alive_window(self):
        adapter = self._mount_adapter(keep_alive_seconds=10)
        r1 = self.session.get(self.url)
        pool = adapter.poolmanager.connection_from_url(self.url)
        opened_at_1 = dict(pool._conn_opened_at)

        r2 = self.session.get(self.url)
        opened_at_2 = dict(pool._conn_opened_at)

        assert r1.status_code == r2.status_code == 200
        assert opened_at_1 == opened_at_2, "same connection object/timestamp should be reused"

    def test_lazy_recycle_on_checkout_after_keep_alive_expires(self):
        from unittest.mock import patch as mock_patch

        from phonepe.sdk.pg.common.http_client_modules.recycling_http_adapter import (
            _RecyclingPoolMixin,
        )

        adapter = self._mount_adapter(keep_alive_seconds=1)
        # Isolate the lazy (checkout-time) recycling mechanism from the background sweep.
        adapter._sweep_stop_event.set()

        # Patch the mixin CLASS method (not a specific pool instance) so we reliably capture
        # whichever pool/conn actually serves each request, and track (pool, conn) pairs in
        # call order - urllib3 can internally retry _get_conn() once for a broken connection,
        # so the LAST entry per request is the one that actually succeeded.
        checked_out = []  # list of (pool, conn) in call order
        orig_get_conn = _RecyclingPoolMixin._get_conn

        def _recording_get_conn(self_pool, timeout=None):
            conn = orig_get_conn(self_pool, timeout=timeout)
            checked_out.append((self_pool, conn))
            return conn

        with mock_patch.object(_RecyclingPoolMixin, "_get_conn", _recording_get_conn):
            r1 = self.session.get(self.url)
            assert checked_out, "no connection was checked out for the first request"
            pool_1, conn_1 = checked_out[-1]
            opened_at_1 = pool_1._conn_opened_at.get(conn_1)
            assert opened_at_1 is not None, "the connection serving r1 should be tracked"

            time.sleep(1.5)  # exceed the 1s keep-alive
            r2 = self.session.get(self.url)
            assert len(checked_out) >= 2, "no connection was checked out for the second request"
            pool_2, conn_2 = checked_out[-1]
            opened_at_2 = pool_2._conn_opened_at.get(conn_2)

        assert r1.status_code == r2.status_code == 200
        assert opened_at_2 is not None, "the connection serving r2 should still be tracked"
        assert opened_at_2 > opened_at_1, (
            "connection should have been recycled (fresh timestamp) once checked out past keep-alive"
        )

    def test_background_sweep_evicts_idle_connection_with_zero_request_activity(self):
        # keep_alive_seconds=1 -> sweep_interval = max(1.0, 0.5) = 1.0s
        adapter = self._mount_adapter(keep_alive_seconds=1)
        self.session.get(self.url)
        pool = adapter.poolmanager.connection_from_url(self.url)
        assert not pool.pool.empty()

        # No further requests at all - only the background sweep thread can evict this.
        time.sleep(2.0)

        idle_item = pool.pool.get_nowait()
        pool.pool.put(idle_item)  # put back immediately so the pool is left usable
        assert idle_item is None, (
            "background sweep should have proactively evicted the idle connection "
            "(freeing the slot to None) with zero request activity"
        )

        # A subsequent request should still succeed via a fresh, transparent reconnect.
        r = self.session.get(self.url)
        assert r.status_code == 200

    def test_close_stops_sweep_thread_and_is_idempotent(self):
        adapter = self._mount_adapter(keep_alive_seconds=5)
        self.session.get(self.url)
        assert adapter._sweep_thread.is_alive()

        adapter.close()
        time.sleep(0.2)
        assert not adapter._sweep_thread.is_alive()

        adapter.close()  # calling again (e.g. via Session.close() mounting twice) must not raise

    def test_sweep_interval_is_half_keep_alive_with_a_floor(self):
        for keep_alive_seconds, expected_interval in [(10, 5.0), (1, 1.0), (0.2, 1.0)]:
            adapter = RecyclingHTTPAdapter(keep_alive_seconds=keep_alive_seconds)
            try:
                assert adapter._sweep_interval_seconds == expected_interval
            finally:
                adapter.close()

    def test_sweep_survives_a_connection_that_fails_to_close(self):
        # Regression test: a connection whose underlying socket is already broken can itself
        # raise when .close() is called on it. If that exception were allowed to abort the
        # sweep mid-loop, every not-yet-processed item drained from the pool queue in that
        # pass would be silently lost, permanently shrinking the pool below its configured
        # maxsize. Every item must be handled independently so one bad connection can't take
        # the rest of the pool's capacity down with it.
        from phonepe.sdk.pg.common.http_client_modules.recycling_http_adapter import (
            RecyclingHTTPConnectionPool,
        )

        class _RaisingCloseConn:
            def close(self):
                raise OSError("simulated broken socket on close()")

        class _NormalConn:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        pool = RecyclingHTTPConnectionPool("example.com", 443, maxsize=3)
        self.addCleanup(pool.close)
        for _ in range(3):
            pool.pool.get_nowait()  # drain the auto-filled None placeholders

        now = time.time()
        conn_a, conn_b, conn_c = _NormalConn(), _RaisingCloseConn(), _NormalConn()
        for conn in (conn_a, conn_b, conn_c):
            pool._conn_opened_at[conn] = now - 100  # well past any reasonable keep-alive
            pool.pool.put(conn)

        pool._evict_idle_connections(keep_alive_seconds=60)

        items = []
        import queue
        try:
            while True:
                items.append(pool.pool.get_nowait())
        except queue.Empty:
            pass
        for item in items:
            pool.pool.put(item)

        assert len(items) == 3, f"pool capacity was lost: expected 3 slots, got {len(items)}"
        assert conn_a.closed
        assert all(item is None for item in items), "all three should have been evicted to None"

    def test_sweep_survives_queue_full_on_a_none_placeholder(self):
        # Regression test: re-queueing a None pool-slot placeholder can itself raise queue.Full
        # (e.g. a concurrent request's own _put_conn() raced in first). The except handler must
        # not then try to weakly reference None when dropping its tracking entry - that raised
        # TypeError and aborted the whole sweep loop, permanently losing every remaining slot.
        import queue
        from unittest.mock import patch

        from phonepe.sdk.pg.common.http_client_modules.recycling_http_adapter import (
            RecyclingHTTPConnectionPool,
        )

        pool = RecyclingHTTPConnectionPool("example.com", 443, maxsize=3)
        self.addCleanup(pool.close)
        for _ in range(3):
            pool.pool.get_nowait()
        for _ in range(3):
            pool.pool.put(None)

        orig_put = pool.pool.put
        call_count = [0]

        def flaky_put(item, block=False):
            call_count[0] += 1
            if call_count[0] == 1:
                raise queue.Full()
            return orig_put(item, block=block)

        with patch.object(pool.pool, "put", side_effect=flaky_put):
            pool._evict_idle_connections(keep_alive_seconds=60)  # must not raise TypeError

        assert pool.pool.qsize() == 3, "pool capacity was lost after a queue.Full on a None item"

    def test_conn_opened_at_does_not_leak_or_misattribute_after_gc(self):
        # Regression test: a connection discarded outside our eviction paths (e.g. queue.Full,
        # or urllib3 discarding a broken connection) must not leak its tracking entry forever,
        # nor risk a later connection reusing the same id() and inheriting a stale timestamp.
        import gc

        from phonepe.sdk.pg.common.http_client_modules.recycling_http_adapter import (
            RecyclingHTTPConnectionPool,
        )

        pool = RecyclingHTTPConnectionPool("example.com", 443, maxsize=1)
        self.addCleanup(pool.close)

        class _Conn:
            pass

        conn = _Conn()
        pool._conn_opened_at[conn] = time.time() - 10_000  # deliberately very stale
        assert len(pool._conn_opened_at) == 1

        del conn  # simulate a discard OUTSIDE our own eviction/lazy-recycle code paths
        gc.collect()

        assert len(pool._conn_opened_at) == 0, (
            "stale entry must be dropped automatically once its connection is garbage "
            "collected - a plain id()-keyed dict would leak this entry forever and risk "
            "misattributing it to an unrelated future connection reusing the same id()"
        )



class TestPoolBlocking(TestCase):
    """Without pool_block=True, urllib3 lets a burst of concurrent requests overflow the pool
    with throwaway, unpooled connections instead of waiting for a pooled slot - so pool_size
    stops being a real limit and every overflow request pays a fresh TCP/TLS handshake."""

    def setUp(self):
        self.server = _ThreadingHTTPServer(("127.0.0.1", 0), _SlowHandler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.shutdown)

    def _connections_opened_for_concurrent_burst(self, http_client_config, burst):
        command = BaseHttpCommand(host_url=f"http://127.0.0.1:{self.port}",
                                  http_client_config=http_client_config)
        self.addCleanup(command.close)

        errors = []

        def _one():
            try:
                command.request(url="/", method=HttpMethodType.GET)
            except Exception as exception:  # pragma: no cover - only on an unexpected failure
                errors.append(exception)

        threads = [threading.Thread(target=_one) for _ in range(burst)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        assert not errors, f"requests failed: {errors}"
        assert not any(thread.is_alive() for thread in threads), "a request never completed"

        pool_manager = command._session.get_adapter(f"http://127.0.0.1:{self.port}/").poolmanager
        pool = pool_manager.pools[list(pool_manager.pools.keys())[0]]
        # num_connections counts every TCP connection urllib3 opened for this pool, including
        # the overflow ones it discarded right after use.
        return pool.num_connections

    def test_concurrent_burst_does_not_exceed_pool_size_by_default(self):
        opened = self._connections_opened_for_concurrent_burst(
            HttpClientConfig(pool_size=2, read_timeout_seconds=10), burst=6)
        assert opened <= 2, (
            f"opened {opened} connections for a pool_size=2 pool - requests overflowed the pool "
            "with unpooled connections instead of waiting for a free slot"
        )

    def test_pool_block_can_be_disabled(self):
        opened = self._connections_opened_for_concurrent_burst(
            HttpClientConfig(pool_size=2, read_timeout_seconds=10, pool_block=False), burst=6)
        assert opened > 2, (
            f"pool_block=False should allow overflow connections, but only {opened} were opened"
        )

    def test_pool_block_defaults_to_true_and_reaches_the_pool(self):
        command = BaseHttpCommand(host_url=f"http://127.0.0.1:{self.port}",
                                  http_client_config=HttpClientConfig())
        self.addCleanup(command.close)
        assert HttpClientConfig().pool_block is True
        pool = command._session.get_adapter("http://x/").poolmanager.connection_from_url(
            f"http://127.0.0.1:{self.port}/")
        assert pool.block is True, "pool_block never reached the underlying urllib3 pool"
