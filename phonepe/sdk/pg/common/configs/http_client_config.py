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

from dataclasses import dataclass


@dataclass(frozen=True)
class HttpClientConfig:
    """Tunable HTTP connection-pool and timeout settings for a PhonePe SDK client instance.

    These four settings travel together and trade off against each other based on a merchant's
    traffic profile:

    - A high-throughput merchant (many concurrent requests) typically wants a larger
      `pool_size` so requests don't queue up waiting for a free pooled connection, and may
      want a smaller `read_timeout_seconds` since their own infrastructure is fast and a slow
      response is more likely a genuine problem worth failing fast on.
    - A low-throughput merchant (e.g. one request every several seconds) or one running on
      slower infrastructure typically needs only a small `pool_size` (2-4 is often enough -
      the default of 10 would sit mostly idle) but may want a larger `read_timeout_seconds` to
      tolerate their own slower network/processing before giving up on a response.

    See the SDK README's "Connection pool & timeout tuning" section for worked examples.

    Attributes
    ----------
    pool_size: int
        Maximum number of pooled (kept-alive) connections per host. Default 10.
    keep_alive_seconds: float
        Maximum time a pooled connection is allowed to sit idle before the SDK proactively
        closes and replaces it with a fresh one on its next use, rather than risking handing a
        request a connection the server/load-balancer may have already silently closed.
        Default 60 seconds.
    connect_timeout_seconds: float
        Maximum time to wait while establishing the TCP/TLS connection. Default 3 seconds.
    read_timeout_seconds: float
        Maximum time to wait for the server to send a response once the request has been sent.
        Default 30 seconds (generous enough to accommodate slower endpoints such as autoPay
        APIs).
    """

    pool_size: int = 10
    keep_alive_seconds: float = 60
    connect_timeout_seconds: float = 3
    read_timeout_seconds: float = 30

    def __post_init__(self):
        if self.pool_size <= 0:
            raise ValueError(f"pool_size must be positive, got {self.pool_size}")
        if self.keep_alive_seconds <= 0:
            raise ValueError(f"keep_alive_seconds must be positive, got {self.keep_alive_seconds}")
        if self.connect_timeout_seconds <= 0:
            raise ValueError(f"connect_timeout_seconds must be positive, got {self.connect_timeout_seconds}")
        if self.read_timeout_seconds <= 0:
            raise ValueError(f"read_timeout_seconds must be positive, got {self.read_timeout_seconds}")
