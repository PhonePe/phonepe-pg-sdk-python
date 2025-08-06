# PhonePe B2B PG SDK

A python library for integrating with PhonePe APIs.

## Installation

Requires `python 3.9` or later

```ssh
pip install --index-url https://phonepe.mycloudrepo.io/public/repositories/phonepe-pg-sdk-python  --extra-index-url https://pypi.org/simple phonepe_sdk
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


## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request