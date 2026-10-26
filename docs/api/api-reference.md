# API reference

Swagger UI: http://127.0.0.1:8000/docs. OpenAPI: http://127.0.0.1:8000/openapi.json.
Generated request/response schemas are authoritative; no per-app response duplication.
Collection limits are 1..100, cursors opaque, and sort/filter predicates are allowlisted.

## Functional endpoints

- `GET /health/live` — Live. Public transport; endpoint-specific rate/provider verification applies.
- `GET /health/ready` — Ready. Public transport; endpoint-specific rate/provider verification applies.
- `GET /api/v1/me` — Me. Bearer plus resource/scope authorization.
- `POST /api/v1/auth/register` — Register. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/auth/login` — Login. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/auth/refresh` — Refresh. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/auth/logout` — Logout. Bearer plus resource/scope authorization.
- `GET /api/v1/roles` — Roles. Bearer plus resource/scope authorization.
- `GET /api/v1/memberships` — Memberships. Bearer plus resource/scope authorization.
- `POST /api/v1/auth/challenges` — Challenge. Bearer plus resource/scope authorization.
- `POST /api/v1/auth/challenges/{challenge_id}/consume` — Consume Challenge. Bearer plus resource/scope authorization.
- `POST /api/v1/organizations` — Organization. Bearer plus resource/scope authorization.
- `POST /api/v1/organizations/{organization_id}/members` — Member. Bearer plus resource/scope authorization.
- `POST /api/v1/geo/countries` — Create Country. Bearer plus resource/scope authorization.
- `GET /api/v1/geo/countries` — Countries. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/geo/cities` — City. Bearer plus resource/scope authorization.
- `GET /api/v1/geo/cities` — Cities. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/geo/zones` — Zone. Bearer plus resource/scope authorization.
- `POST /api/v1/addresses` — Address. Bearer plus resource/scope authorization.
- `GET /api/v1/addresses` — Addresses. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/brands` — Brand. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/branches` — Branch. Bearer plus resource/scope authorization.
- `GET /api/v1/merchants/branches` — Branches. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/merchants/branches/{branch_id}/review` — Review Branch. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/branches/{branch_id}/hours` — Hours. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/branches/{branch_id}/capabilities` — Capability. Bearer plus resource/scope authorization.
- `POST /api/v1/catalog/categories` — Category. Bearer plus resource/scope authorization.
- `GET /api/v1/catalog/categories` — Categories. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/catalog/products` — Product. Bearer plus resource/scope authorization.
- `POST /api/v1/catalog/products/{product_id}/variants` — Variant. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/branches/{branch_id}/prices` — Price. Bearer plus resource/scope authorization.
- `GET /api/v1/merchants/branches/{branch_id}/prices` — Prices. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/merchants/branches/{branch_id}/windows` — Window. Bearer plus resource/scope authorization.
- `GET /api/v1/merchants/branches/{branch_id}/windows` — Windows. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/inventory/branches/{branch_id}/adjustments` — Adjust Stock. Bearer plus resource/scope authorization.
- `POST /api/v1/inventory/branches/{branch_id}/batches` — Receive Batch. Bearer plus resource/scope authorization.
- `GET /api/v1/inventory/branches/{branch_id}` — Stock Status. Bearer plus resource/scope authorization.
- `POST /api/v1/carts` — Cart. Bearer plus resource/scope authorization.
- `POST /api/v1/carts/{cart_id}/items` — Cart Item. Bearer plus resource/scope authorization.
- `GET /api/v1/carts/{cart_id}/items` — Cart Items. Bearer plus resource/scope authorization.
- `DELETE /api/v1/carts/{cart_id}/items/{item_id}` — Remove Item. Bearer plus resource/scope authorization.
- `PATCH /api/v1/carts/{cart_id}/items/{item_id}` — Quantity. Bearer plus resource/scope authorization.
- `POST /api/v1/carts/{cart_id}/quote` — Quote. Bearer plus resource/scope authorization.
- `POST /api/v1/orders/confirm` — Confirm. Bearer plus resource/scope authorization.
- `GET /api/v1/orders` — Orders. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}` — Order. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}/merchant-orders` — Children. Bearer plus resource/scope authorization.
- `POST /api/v1/merchant-orders/{child_id}/transition` — Child Transition. Bearer plus resource/scope authorization.
- `POST /api/v1/pilots` — Pilot. Bearer plus resource/scope authorization.
- `POST /api/v1/pilots/{pilot_id}/verify` — Verify Pilot. Bearer plus resource/scope authorization.
- `PUT /api/v1/pilots/{pilot_id}/availability` — Availability. Bearer plus resource/scope authorization.
- `PUT /api/v1/pilots/{pilot_id}/location` — Location. Bearer plus resource/scope authorization.
- `POST /api/v1/delivery-tasks/{task_id}/offer` — Offer. Bearer plus resource/scope authorization.
- `POST /api/v1/pilot-assignments/{assignment_id}/accept` — Accept. Bearer plus resource/scope authorization.
- `POST /api/v1/delivery-tasks/{task_id}/pickup` — Pickup. Bearer plus resource/scope authorization.
- `POST /api/v1/delivery-tasks/{task_id}/fail` — Fail. Bearer plus resource/scope authorization.
- `POST /api/v1/delivery-tasks/{task_id}/acknowledge` — Acknowledge. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/currencies` — Currency. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/accounts` — Account. Bearer plus resource/scope authorization.
- `POST /api/v1/organizations/{organization_id}/legal-entities` — Legal Entity. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/books` — Ledger Book. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/journals` — Journal. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/journals/{journal_id}/reversal` — Reversal. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/sandbox/payment-intents` — Payment. Bearer plus resource/scope authorization.
- `GET /api/v1/finance/payments/{payment_id}` — Payment Status. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/sandbox/webhook` — Sandbox Webhook. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/finance/sandbox/payments/{payment_id}/refunds` — Refund. Bearer plus resource/scope authorization.
- `POST /api/v1/support/tickets` — Ticket. Bearer plus resource/scope authorization.
- `POST /api/v1/support/tickets/{ticket_id}/messages` — Message. Bearer plus resource/scope authorization.
- `GET /api/v1/audit/events` — Audit Events. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/refund-approvals` — Request Refund Approval. Bearer plus resource/scope authorization.
- `POST /api/v1/finance/refund-approvals/{approval_id}/decision` — Decide Refund. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}/history` — Order History. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}/delivery-tasks` — Order Tasks. Bearer plus resource/scope authorization.
- `GET /api/v1/inventory/branches/{branch_id}/movements` — Stock Movements. Bearer plus resource/scope authorization.
- `POST /api/v1/geo/serviceability` — Serviceability. Bearer plus resource/scope authorization.
- `POST /api/v1/orders/{order_id}/cancel` — Cancel Order. Bearer plus resource/scope authorization.
- `GET /api/v1/notifications` — Notifications. Bearer plus resource/scope authorization.

## Verification

Use sample-requests.ps1 explicitly for registration/login, cart/checkout, merchant, pilot and support requests.
No default privileged account exists. Provision only a named existing user via the local operator CLI.
Complete real-database examples: tests/integration/helpers.py and test_vertical_slice.py.
See api-security.md and error-contracts.md for authorization, precision, state and error behavior.
Sandbox finance requires explicit enabling and never performs a real financial transaction.
Total documented HTTP operations: 78.
