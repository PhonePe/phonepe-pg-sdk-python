# PhonePe B2B PG SDK

A python library for integrating with PhonePe APIs.

## v3.0.0 - Breaking changes

- **Retry mechanism removed.** The SDK no longer retries any HTTP call (including GET). The
  `should_retry` constructor parameter has been removed from `StandardCheckoutClient`,
  `CustomCheckoutClient`, and `SubscriptionClient` - passing it now raises a `TypeError`.
- **Client construction can now raise.** The SDK fetches its OAuth token immediately at
  construction (a single, non-blocking attempt) instead of waiting for the first API call.
  Genuine configuration problems (e.g. invalid credentials) now fail fast and
  `get_instance(...)`/the constructor raises immediately, where previously construction always
  succeeded regardless of credential validity. See the [Quick start](#quick-start) note below for
  details - transient failures do NOT raise or block; they're retried automatically in the
  background instead.
- **New:** configurable connection pooling/timeouts via `HttpClientConfig` (see
  [Connection pool & timeout tuning](#connection-pool--timeout-tuning)) and a `close()` method on
  every client to release resources cleanly.

## Installation

Requires `python 3.9` or later

```ssh
pip install phonepe-pg-sdk-python
```    

## Quick start

To get your keys, please visit the Merchant Onboarding of PhonePe PG: [Merchant Onboarding](https://developer.phonepe.com/v1/docs/merchant-onboarding)
You will need three things to get started: `client-id`, `client-secret` and `client-version`.

Create an instance of the `StandardCheckoutClient` class:

```python
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.env import Env

client_id = "<YOUR_CLIENT_ID>"
client_secret = "<YOUR_CLIENT_SECRET>"
client_version = 1  # Insert your client version here
env = Env.SANDBOX  # Change to Env.PRODUCTION when you go live

standard_phonepe_client = StandardCheckoutClient.get_instance(client_id=client_id,
                                                              client_secret=client_secret,
                                                              client_version=client_version,
                                                              env=env)
```

> **Note:** Client construction fetches an OAuth token immediately (a single, non-blocking
> attempt) rather than waiting for the first API call. A genuine configuration problem (e.g.
> invalid credentials) fails fast and `get_instance(...)`/the constructor raises immediately; a
> transient failure (network blip, 5xx, rate-limiting) does NOT block construction or raise - it's
> retried automatically in the background instead. Once constructed, the token is kept fresh
> automatically in the background for the lifetime of the client - see
> [Connection pool & timeout tuning](#connection-pool--timeout-tuning) below for `close()` and
> other tunable behavior.

### Initiate an order using Checkout Page

To init a pay request, we make a request object using `StandardCheckoutPayRequest.build_request` [build_request](#standard-checkout-pay-request-builder).

##### Code:

```python
from uuid import uuid4
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest

unique_order_id = str(uuid4())
ui_redirect_url = "https://www.merchant.com/redirect"
amount = 100
standard_pay_request = StandardCheckoutPayRequest.build_request(merchant_order_id=unique_order_id,
                                                                amount=amount,
                                                                redirect_url=ui_redirect_url)
standard_pay_response = standard_phonepe_client.pay(standard_pay_request)
checkout_page_url = standard_pay_response.redirect_url
```

The data will be in a `StandardCheckoutPayResponse` object.
The `checkout_page_url` you get can be handled by redirecting the user to that url on the front end.

### Check status of order

View the state for the order we just initiated.

```python
unique_order_id = "INSERT_YOUR_UNIQUE_ORDER_ID"  
order_status_response = standard_phonepe_client.get_order_status(merchant_order_id=unique_order_id)  
order_state = order_status_response.state
```

You will get the data [OrderStatusResponse](#order-status-response) object.


For more details, please visit: https://developer.phonepe.com 

## Connection pool & timeout tuning

Every client (`StandardCheckoutClient`, `CustomCheckoutClient`, `SubscriptionClient`) accepts an
optional `http_client_config` argument on both its constructor and `get_instance(...)`, letting
you tune the underlying HTTP connection pool and timeouts per merchant/client instance:

```python
from phonepe.sdk.pg.common.configs.http_client_config import HttpClientConfig
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.env import Env

http_client_config = HttpClientConfig(
    pool_size=10,               # max pooled (kept-alive) connections per host
    keep_alive_seconds=60,      # proactively recycle connections idle longer than this
    connect_timeout_seconds=3,  # max time to establish the TCP/TLS connection
    read_timeout_seconds=30,    # max time to wait for a response once the request is sent
)

standard_phonepe_client = StandardCheckoutClient.get_instance(
    client_id=client_id,
    client_secret=client_secret,
    client_version=client_version,
    env=env,
    http_client_config=http_client_config,
)
```

If `http_client_config` is omitted, the SDK uses the defaults shown above (`pool_size=10`,
`keep_alive_seconds=60`, `connect_timeout_seconds=3`, `read_timeout_seconds=30`).

**Why these four settings trade off against each other:**

- **`pool_size`** caps how many connections are kept alive per host. A merchant sending many
  concurrent requests benefits from a larger pool so requests don't queue up waiting for a free
  connection; a merchant sending only the occasional request (e.g. one every several seconds)
  gains nothing from a large pool - a small value (2-4) is enough, since most of those connections
  would otherwise sit idle.
- **`keep_alive_seconds`** bounds how long a pooled connection can sit idle before the SDK
  proactively closes and replaces it with a fresh one, rather than risking handing a request a
  connection that a server/load balancer has already silently closed while idle (a scenario
  confirmed via repro testing against PhonePe's production environment). This is enforced both
  the moment a connection is next reused for a request *and* independently by a background
  sweep thread that periodically closes idle connections directly, so staleness is bounded even
  during a period with no request traffic at all.
- **`connect_timeout_seconds`** / **`read_timeout_seconds`** bound how long a single request is
  allowed to take establishing a connection vs. waiting for a response. A merchant with fast,
  reliable infrastructure can tighten these to fail faster on genuine problems; a merchant on
  slower/less reliable infrastructure (or calling latency-sensitive endpoints like autoPay APIs)
  may need to raise `read_timeout_seconds` to avoid timing out on otherwise-successful, just-slow
  responses.

**Worked examples:**

- **High-throughput merchant** (e.g. many concurrent payment/status requests per second, on solid
  infrastructure): increase `pool_size` (e.g. 20-50) so concurrent requests aren't blocked waiting
  for a free connection, and consider lowering `read_timeout_seconds` (e.g. 10-15s) since a slow
  response is more likely a genuine problem worth failing fast on.
- **Low-throughput / slower-infrastructure merchant** (e.g. one request every several seconds,
  or calling from a network with higher latency): a small `pool_size` (2-4) is plenty - a large
  pool would mostly sit idle - but raise `read_timeout_seconds` (e.g. 45-60s) to tolerate your
  own slower network/processing before giving up on an otherwise-successful response.

### Releasing resources with `close()`

Every client exposes a `close()` method that releases pooled HTTP connections and stops the
background token-refresh thread (see below). This is a daemon thread, so it doesn't prevent your
process from exiting even if you never call `close()` - but short-lived processes (tests, scripts,
serverless invocations) that want a clean, immediate shutdown should call it explicitly:

```python
standard_phonepe_client.close()
```

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request