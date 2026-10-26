# API reference

Local Swagger UI: http://127.0.0.1:8000/docs
OpenAPI: http://127.0.0.1:8000/openapi.json; canonical exported contract: packages/api_contracts/openapi.json.

Each entry below is generated from the current FastAPI contract. Request/response schemas,
input constraints and bearer requirements are available in Swagger and the exported schema.
Collections use limit=1..100 and opaque next_cursor; sorting is fixed UUID order. No arbitrary SQL filters.

- `GET /health/live` — Live. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `GET /health/ready` — Ready. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `GET /api/v1/me` — Me. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/auth/register` — Register. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/auth/login` — Login. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/auth/refresh` — Refresh. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/auth/logout` — Logout. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/roles` — Roles. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/memberships` — Memberships. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/auth/challenges` — Challenge. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/auth/challenges/{challenge_id}/consume` — Consume Challenge. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/organizations` — Organization. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/organizations/{organization_id}/members` — Member. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/geo/countries` — Create Country. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/geo/countries` — Countries. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/geo/cities` — City. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/geo/cities` — Cities. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/geo/zones` — Zone. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/addresses` — Address. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/addresses` — Addresses. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/merchants/brands` — Brand. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/merchants/branches` — Branch. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/merchants/branches` — Branches. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/merchants/branches/{branch_id}/review` — Review Branch. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/merchants/branches/{branch_id}/hours` — Hours. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/merchants/branches/{branch_id}/capabilities` — Capability. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/catalog/categories` — Category. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/catalog/categories` — Categories. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/catalog/products` — Product. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/catalog/products/{product_id}/variants` — Variant. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/merchants/branches/{branch_id}/prices` — Price. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/merchants/branches/{branch_id}/prices` — Prices. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/merchants/branches/{branch_id}/windows` — Window. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/merchants/branches/{branch_id}/windows` — Windows. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/inventory/branches/{branch_id}/adjustments` — Adjust Stock. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/inventory/branches/{branch_id}/batches` — Receive Batch. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/inventory/branches/{branch_id}` — Stock Status. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/carts` — Cart. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/carts/{cart_id}/items` — Cart Item. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/carts/{cart_id}/items` — Cart Items. Bearer identity; additional resource/permission checks apply.
- `DELETE /api/v1/carts/{cart_id}/items/{item_id}` — Remove Item. Bearer identity; additional resource/permission checks apply.
- `PATCH /api/v1/carts/{cart_id}/items/{item_id}` — Quantity. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/carts/{cart_id}/quote` — Quote. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/orders/confirm` — Confirm. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/orders` — Orders. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/orders/{order_id}` — Order. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/orders/{order_id}/merchant-orders` — Children. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/merchant-orders/{child_id}/transition` — Child Transition. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/pilots` — Pilot. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/pilots/{pilot_id}/verify` — Verify Pilot. Bearer identity; additional resource/permission checks apply.
- `PUT /api/v1/pilots/{pilot_id}/availability` — Availability. Bearer identity; additional resource/permission checks apply.
- `PUT /api/v1/pilots/{pilot_id}/location` — Location. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/delivery-tasks/{task_id}/offer` — Offer. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/pilot-assignments/{assignment_id}/accept` — Accept. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/delivery-tasks/{task_id}/pickup` — Pickup. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/delivery-tasks/{task_id}/fail` — Fail. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/delivery-tasks/{task_id}/acknowledge` — Acknowledge. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/currencies` — Currency. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/accounts` — Account. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/organizations/{organization_id}/legal-entities` — Legal Entity. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/books` — Ledger Book. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/journals` — Journal. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/journals/{journal_id}/reversal` — Reversal. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/sandbox/payment-intents` — Payment. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/finance/payments/{payment_id}` — Payment Status. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/sandbox/webhook` — Sandbox Webhook. Public transport; webhook/provider verification or auth rate limits apply where relevant.
- `POST /api/v1/finance/sandbox/payments/{payment_id}/refunds` — Refund. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/support/tickets` — Ticket. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/support/tickets/{ticket_id}/messages` — Message. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/audit/events` — Audit Events. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/refund-approvals` — Request Refund Approval. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/finance/refund-approvals/{approval_id}/decision` — Decide Refund. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/orders/{order_id}/history` — Order History. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/orders/{order_id}/delivery-tasks` — Order Tasks. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/inventory/branches/{branch_id}/movements` — Stock Movements. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/geo/serviceability` — Serviceability. Bearer identity; additional resource/permission checks apply.
- `POST /api/v1/orders/{order_id}/cancel` — Cancel Order. Bearer identity; additional resource/permission checks apply.
- `GET /api/v1/notifications` — Notifications. Bearer identity; additional resource/permission checks apply.

## Local verification sequence

1. Register and login an actual local user. No privileged account exists by default.
2. Grant platform access only through the explicit local CLI to a named existing user if appropriate.
3. Create countries/currencies/categories/cities/zones with authorized admin permissions.
4. A merchant owner creates organization, brand, branch, hours/capabilities, products/variants, stock/prices/windows.
5. A different authorized reviewer approves the branch. Customer adds cart lines and requests a quote.
6. Confirm with Idempotency-Key, accept/prepare merchant children, offer/accept pilot tasks where serviceability is available,
   or verify customer pickup. Recipient acknowledgment completes delivery. Audit/history capture the changes.

Concrete PowerShell requests and a repeatable test-server workflow: sample-requests.ps1.
Full examples against only the dedicated real test database are in tests/integration/helpers.py and test_vertical_slice.py.
Sandbox financial endpoints require explicit configuration and do not perform real transactions.
