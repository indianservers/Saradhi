# Customer checkout flow

1. Customer signs in using the backend email/password endpoints.
2. The customer selects a current branch catalogue item. The add flow reads branch windows and saved addresses, then records a delivery method, address when applicable, and future window on that cart line.
3. Cart ID is stored in platform secure storage. On reopening, the app reads `/carts/{id}` for the current version and `/carts/{id}/items` for lines. Quantity edits send `expected_version`; server conflicts cause a reload.
4. Checkout calls `/carts/{id}/quote`. Price, available inventory, schedule, branch/category serviceability and any configured quote rules are reevaluated by the backend. The app shows returned line detail and total only.
5. Customer confirms using a random quote-scoped `Idempotency-Key`, persisted before the request. If the request outcome is uncertain, the same quote/key pair is reused to avoid duplicate orders.
6. After receiving the actual parent order, a development/test build creates a sandbox intent and requests completion through the authenticated server simulation route. That route signs the existing webhook payload server-side and returns the actual payment status. Production builds do not call it; a production gateway callback is still unconfigured.
7. The order is available in history and its tracking page polls the authorized snapshot.

Delivery windows are per cart line, so a multi-merchant cart can contain different merchant windows. The backend groups lines into merchant orders and fulfillment units. The current app does not promise ASAP delivery; no ASAP contract exists.

The current quote engine rejects unpriced options, variable-weight products, configured taxable products without a tax calculator, mixed currencies, and unavailable price/stock/serviceability. Fees/taxes/discounts are not estimated by the app. Address is manually entered with coordinates because there is no geocoder or map selection provider.
