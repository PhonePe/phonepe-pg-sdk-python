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
import queue
import threading
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

    Two independent mechanisms enforce this:

    1. `_get_conn` (the single choke point where urllib3 either returns a pooled connection or
       mints a new one) is overridden to track how long each connection object has been alive
       and proactively `.close()` any reused connection whose age exceeds `keep_alive_seconds`
       *before* handing it back. This only fires the next time a request actually checks the
       connection out, though - it cannot help a connection that's simply sitting idle with no
       request activity at all.
    2. `_evict_idle_connections` (called periodically by RecyclingHTTPAdapter's background
       sweep thread - see below) proactively closes idle connections directly in the pool,
       independently of whether any request ever checks them out again. This bounds how stale
       a connection can get even during a long period with zero traffic.

    Either way, closing sets the connection's `.sock` back to `None`, so urllib3's own
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

    def _evict_idle_connections(self, keep_alive_seconds):
        """Proactively closes any IDLE connection (currently sitting in the pool, not checked
        out for an in-flight request) older than keep_alive_seconds. Called periodically by
        RecyclingHTTPAdapter's background sweep thread, independently of request activity -
        this is what bounds staleness even when nothing has tried to reuse a connection in a
        while, which `_get_conn` above cannot do on its own (it only runs on checkout).

        `self.pool` is a fixed-size urllib3 queue.LifoQueue holding one entry per available
        pool slot: either an idle connection object ready for reuse, or a None placeholder for
        a slot with nothing pooled in it yet. We drain it, close+discard anything too old
        (replacing it with a None placeholder to free that slot), and put everything back.
        This isn't perfectly atomic against a concurrent request's own _get_conn()/_put_conn()
        - at worst, a request racing with this sweep briefly sees an empty pool and mints a new
        connection instead of reusing one, which is the same harmless fallback urllib3 already
        uses whenever the pool happens to be empty.

        Every drained item is handled in its OWN try/except: closing a connection whose
        underlying socket is already broken (e.g. the peer reset it while idle) can itself
        raise, and if that exception were allowed to escape mid-loop, every item still waiting
        to be re-queued would be silently dropped, permanently shrinking the pool's capacity by
        however many items hadn't been processed yet. Isolating each item's handling guarantees
        every single drained item - whether closed, kept, or itself broken - is always put
        back in some form (the original connection, a fresh None slot, or worst case a bare
        None so the slot count is never lost).
        """
        pool = self.pool
        if pool is None:
            return  # pool already closed
        now = time.time()
        items = []
        try:
            while True:
                items.append(pool.get_nowait())
        except queue.Empty:
            pass

        evicted_count = 0
        for item in items:
            try:
                if item is None:
                    pool.put(None, block=False)
                    continue
                opened_at = self._conn_opened_at.get(id(item))
                if opened_at is not None and (now - opened_at) > keep_alive_seconds:
                    item.close()
                    self._conn_opened_at.pop(id(item), None)
                    pool.put(None, block=False)
                    evicted_count += 1
                else:
                    pool.put(item, block=False)
            except Exception:
                # Closing (or re-queueing) this one item failed - log it, drop tracking for it
                # so it can't be mistaken for a still-valid connection, but still free its slot
                # with a None placeholder rather than losing the slot from the pool entirely.
                logging.exception(
                    "Error while proactively evicting a pooled connection; freeing its slot anyway"
                )
                self._conn_opened_at.pop(id(item), None)
                try:
                    pool.put(None, block=False)
                except Exception:
                    logging.exception("Could not even free the slot for a connection that failed to evict")
        if evicted_count:
            logging.info(f"Proactively evicted {evicted_count} idle connection(s) past keep_alive_seconds")


class RecyclingHTTPConnectionPool(_RecyclingPoolMixin, HTTPConnectionPool):
    pass


class RecyclingHTTPSConnectionPool(_RecyclingPoolMixin, HTTPSConnectionPool):
    pass


class RecyclingHTTPAdapter(HTTPAdapter):
    """A requests HTTPAdapter that proactively recycles pooled connections older than
    `keep_alive_seconds`, on top of the usual pool_connections/pool_maxsize sizing.

    Enforcement happens two ways: lazily, the next time an aged-out connection is checked out
    for a request (see _RecyclingPoolMixin._get_conn), and proactively, via a background sweep
    thread (started here) that periodically scans idle pooled connections and closes any that
    have exceeded keep_alive_seconds - even if nothing has tried to reuse them. The sweep runs
    roughly twice as often as keep_alive_seconds, so an idle connection is never left waiting
    much longer than ~1.5x keep_alive_seconds before being caught, regardless of request
    traffic.

    The pool-class override below is applied to this adapter's own `PoolManager` instance only
    (`pool_classes_by_scheme` is set fresh per-PoolManager in urllib3, never shared class/global
    state), so multiple BaseHttpCommand instances - potentially with different HttpClientConfig
    settings - can safely coexist in the same merchant process without interfering with each
    other or with any other library's use of requests/urllib3 in that process. The background
    sweep thread is likewise private to this one adapter instance.
    """

    def __init__(self, *args, keep_alive_seconds=60, **kwargs):
        self._keep_alive_seconds = keep_alive_seconds
        self._sweep_interval_seconds = max(1.0, keep_alive_seconds / 2)
        self._sweep_stop_event = threading.Event()
        self._sweep_thread = None
        super().__init__(*args, **kwargs)
        self._sweep_thread = threading.Thread(
            target=self._sweep_loop, name="RecyclingHTTPAdapterSweeper", daemon=True,
        )
        self._sweep_thread.start()

    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)
        self.poolmanager.pool_classes_by_scheme = {
            "http": partial(RecyclingHTTPConnectionPool, keep_alive_seconds=self._keep_alive_seconds),
            "https": partial(RecyclingHTTPSConnectionPool, keep_alive_seconds=self._keep_alive_seconds),
        }

    def _sweep_loop(self):
        while not self._sweep_stop_event.wait(timeout=self._sweep_interval_seconds):
            try:
                # RecentlyUsedContainer (urllib3's PoolManager.pools) deliberately raises on
                # __iter__/.values() since that's not thread-safe against concurrent pool
                # creation - but .keys() IS thread-safe (lock-protected, returns a real list),
                # and so is __getitem__, so we look each pool up individually by key instead.
                for key in self.poolmanager.pools.keys():
                    try:
                        pool = self.poolmanager.pools[key]
                    except KeyError:
                        continue  # evicted between .keys() and lookup - already gone, skip it
                    evict = getattr(pool, "_evict_idle_connections", None)
                    if evict is not None:
                        evict(self._keep_alive_seconds)
            except Exception:
                # Defensive: never let an unexpected error (e.g. a pool closed mid-sweep) kill
                # this daemon thread silently.
                logging.exception("Unexpected error while proactively sweeping idle connections")

    def close(self):
        """Stops the background sweep thread and releases pooled connections. Safe to call
        multiple times (e.g. requests.Session.close() calls this once per mounted scheme, and
        this same adapter instance is mounted for both http:// and https://)."""
        self._sweep_stop_event.set()
        if self._sweep_thread is not None and self._sweep_thread.is_alive():
            self._sweep_thread.join(timeout=2)
        super().close()
