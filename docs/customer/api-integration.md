# Customer API integration

The app uses `Dio` from `packages/flutter_networking`. `API_BASE_URL` can be supplied at build time. Without an override, Android emulator uses `http://10.0.2.2:8000`; iOS simulator uses `http://localhost:8000`. Physical devices need a reachable host override. Production transport rejects non-HTTPS URLs.

## Identity and session

- `POST /api/v1/auth/register` with email/password, followed by `POST /api/v1/auth/login`.
- Tokens are stored with `flutter_secure_storage`; a 401 triggers one refresh using `/auth/refresh`, then retries the original request once.
- Sign-out calls `/auth/logout` and clears local token/cart state even if the API is offline.
- Phone OTP registration/recovery is unavailable and is not simulated.

## Discovery and commerce

- `GET /api/v1/merchants/branches?limit=...` for public approved/accepting branch discovery.
- `GET /api/v1/catalog/products` requires a customer Actor. Optional `city_id`, `branch_id`, `category_id`, `merchant_type`, `q`, `cursor`, and bounded `limit` filters. It returns product/variant, branch/category, active price, currency and sellable stock.
- `GET /api/v1/merchants/branches/{branch_id}/windows` provides future merchant windows.
- `GET/POST /api/v1/addresses` list and create owner-scoped addresses.
- Cart lifecycle: `POST /carts`, `GET /carts/{id}`, `POST/GET/PATCH/DELETE /carts/{id}/items`, `POST /carts/{id}/quote`, and `POST /orders/confirm`.
- Quote contains lines from the server snapshot. Confirm uses the required `Idempotency-Key` header. Keys are stored in secure storage by quote ID for timeout recovery.

## Order lifecycle

- `GET /orders`, `GET /orders/{id}`, `GET /orders/{id}/tracking` are owner-authorized.
- `POST /finance/sandbox/payment-intents` is called after order confirmation. In development/test, `POST /finance/sandbox/payments/{payment_id}/complete` performs an owner-checked server-side signed simulation through the normal webhook handler. Flutter never constructs signatures.
- `POST /support/tickets` can open an owned-order or general ticket. Customer ticket progress is unavailable.

All screens distinguish loading, empty, error and provider-unavailable results. Cursors are returned by APIs; current app screens consume the initial bounded result page.
