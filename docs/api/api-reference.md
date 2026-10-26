# API reference

Swagger UI: http://127.0.0.1:8000/docs. OpenAPI: http://127.0.0.1:8000/openapi.json.
Generated request/response schemas are authoritative; no per-app response duplication.
Collection limits are 1..100, cursors opaque, and sort/filter predicates are allowlisted.

## Functional endpoints

- `GET /health/live` — Live. Public transport; endpoint-specific rate/provider verification applies.
- `GET /health/capabilities` — Capabilities. Public transport; endpoint-specific rate/provider verification applies.
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
- `POST /api/v1/merchant/onboarding` — Merchant Onboarding. Bearer plus resource/scope authorization.
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
- `GET /api/v1/merchant/branches` — Merchant Branches. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/branches/{branch_id}/review` — Review Branch. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/branches/{branch_id}/hours` — Hours. Bearer plus resource/scope authorization.
- `PUT /api/v1/merchant/branches/{branch_id}/availability` — Merchant Availability. Bearer plus resource/scope authorization.
- `GET /api/v1/merchant/branches/{branch_id}/catalog` — Merchant Catalog. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/branches/{branch_id}/capabilities` — Capability. Bearer plus resource/scope authorization.
- `POST /api/v1/catalog/categories` — Category. Bearer plus resource/scope authorization.
- `GET /api/v1/catalog/categories` — Categories. Public transport; endpoint-specific rate/provider verification applies.
- `GET /api/v1/catalog/products` — Customer Catalog. Bearer plus resource/scope authorization.
- `POST /api/v1/catalog/products` — Product. Bearer plus resource/scope authorization.
- `POST /api/v1/catalog/products/{product_id}/variants` — Variant. Bearer plus resource/scope authorization.
- `POST /api/v1/merchants/branches/{branch_id}/prices` — Price. Bearer plus resource/scope authorization.
- `GET /api/v1/merchants/branches/{branch_id}/prices` — Prices. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/merchants/branches/{branch_id}/windows` — Window. Bearer plus resource/scope authorization.
- `GET /api/v1/merchants/branches/{branch_id}/windows` — Windows. Public transport; endpoint-specific rate/provider verification applies.
- `POST /api/v1/inventory/branches/{branch_id}/adjustments` — Adjust Stock. Bearer plus resource/scope authorization.
- `POST /api/v1/inventory/branches/{branch_id}/batches` — Receive Batch. Bearer plus resource/scope authorization.
- `GET /api/v1/inventory/branches/{branch_id}/batches` — Stock Batches. Bearer plus resource/scope authorization.
- `GET /api/v1/inventory/branches/{branch_id}` — Stock Status. Bearer plus resource/scope authorization.
- `POST /api/v1/carts` — Cart. Bearer plus resource/scope authorization.
- `GET /api/v1/carts/{cart_id}` — Get Cart. Bearer plus resource/scope authorization.
- `POST /api/v1/carts/{cart_id}/items` — Cart Item. Bearer plus resource/scope authorization.
- `GET /api/v1/carts/{cart_id}/items` — Cart Items. Bearer plus resource/scope authorization.
- `DELETE /api/v1/carts/{cart_id}/items/{item_id}` — Remove Item. Bearer plus resource/scope authorization.
- `PATCH /api/v1/carts/{cart_id}/items/{item_id}` — Quantity. Bearer plus resource/scope authorization.
- `POST /api/v1/carts/{cart_id}/quote` — Quote. Bearer plus resource/scope authorization.
- `POST /api/v1/orders/confirm` — Confirm. Bearer plus resource/scope authorization.
- `GET /api/v1/orders` — Orders. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}` — Order. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}/payment` — Order Payment. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}/merchant-orders` — Children. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}/reorder-lines` — Reorder Lines. Bearer plus resource/scope authorization.
- `GET /api/v1/merchant/branches/{branch_id}/orders` — Merchant Order Queue. Bearer plus resource/scope authorization.
- `POST /api/v1/merchant/branches/{branch_id}/kitchen/stations` — Create Kitchen Station. Bearer plus resource/scope authorization.
- `GET /api/v1/merchant/branches/{branch_id}/kitchen/stations` — Kitchen Stations. Bearer plus resource/scope authorization.
- `GET /api/v1/merchant/branches/{branch_id}/kitchen/tasks` — Kitchen Tasks. Bearer plus resource/scope authorization.
- `PUT /api/v1/merchant/kitchen/tasks/{task_id}/station` — Reassign Kitchen Task. Bearer plus resource/scope authorization.
- `POST /api/v1/merchant/kitchen/tasks/{task_id}/transition` — Transition Kitchen Task. Bearer plus resource/scope authorization.
- `POST /api/v1/merchant-orders/{child_id}/transition` — Child Transition. Bearer plus resource/scope authorization.
- `POST /api/v1/pilots` — Pilot. Bearer plus resource/scope authorization.
- `POST /api/v1/pilots/{pilot_id}/verify` — Verify Pilot. Bearer plus resource/scope authorization.
- `PUT /api/v1/pilots/{pilot_id}/availability` — Availability. Bearer plus resource/scope authorization.
- `POST /api/v1/pilots/me/availability` — My Availability. Bearer plus resource/scope authorization.
- `GET /api/v1/pilots/me` — My Pilot Profile. Bearer plus resource/scope authorization.
- `GET /api/v1/pilots/me/assignments` — My Pilot Assignments. Bearer plus resource/scope authorization.
- `GET /api/v1/pilots/me/earnings` — My Pilot Earnings. Bearer plus resource/scope authorization.
- `GET /api/v1/pilots/me/operations` — My Pilot Operations. Bearer plus resource/scope authorization.
- `GET /api/v1/pilots/me/supply-demand` — My Pilot Supply Demand. Bearer plus resource/scope authorization.
- `POST /api/v1/pilots/me/incidents` — Report Pilot Incident. Bearer plus resource/scope authorization.
- `GET /api/v1/pilots/me/incidents` — My Pilot Incidents. Bearer plus resource/scope authorization.
- `POST /api/v1/pilots/me/location-consent` — Pilot Location Consent. Bearer plus resource/scope authorization.
- `POST /api/v1/pilots/me/location` — My Location. Bearer plus resource/scope authorization.
- `GET /api/v1/orders/{order_id}/tracking` — Order Tracking. Bearer plus resource/scope authorization.
- `GET /api/v1/deliveries/{delivery_id}` — Delivery Snapshot. Bearer plus resource/scope authorization.
- `GET /api/v1/deliveries/{delivery_id}/timeline` — Delivery Timeline. Bearer plus resource/scope authorization.
- `GET /api/v1/deliveries/{delivery_id}/eta` — Delivery Eta. Bearer plus resource/scope authorization.
- `POST /api/v1/realtime/tickets` — Realtime Ticket. Bearer plus resource/scope authorization.
- `PUT /api/v1/pilots/{pilot_id}/location` — Location. Bearer plus resource/scope authorization.
- `POST /api/v1/delivery-tasks/{task_id}/offer` — Offer. Bearer plus resource/scope authorization.
- `POST /api/v1/pilot-assignments/{assignment_id}/accept` — Accept. Bearer plus resource/scope authorization.
- `POST /api/v1/pilot-assignments/{assignment_id}/reject` — Reject Assignment. Bearer plus resource/scope authorization.
- `GET /api/v1/operations/cities/{city_id}/pilot-incidents` — City Pilot Incidents. Bearer plus resource/scope authorization.
- `POST /api/v1/operations/pilot-incidents/{incident_id}/acknowledge` — Acknowledge Pilot Incident. Bearer plus resource/scope authorization.
- `POST /api/v1/operations/pilot-incidents/{incident_id}/resolve` — Resolve Pilot Incident. Bearer plus resource/scope authorization.
- `GET /api/v1/operations/cities/{city_id}/dispatch` — City Dispatch. Bearer plus resource/scope authorization.
- `GET /api/v1/operations/cities/{city_id}/fleet` — City Fleet. Bearer plus resource/scope authorization.
- `GET /api/v1/ai/demand/cities/{city_id}/forecast` — Ai City Forecast. Bearer plus resource/scope authorization.
- `GET /api/v1/ai/demand/zones/{zone_id}/forecast` — Ai Zone Forecast. Bearer plus resource/scope authorization.
- `POST /api/v1/ai/preparation/predict` — Ai Preparation Predict. Bearer plus resource/scope authorization.
- `GET /api/v1/ai/positioning/zones/{zone_id}/recommendations` — Ai Positioning. Bearer plus resource/scope authorization.
- `POST /api/v1/ai/dispatch/optimize` — Ai Dispatch Optimize. Bearer plus resource/scope authorization.
- `POST /api/v1/ai/dispatch/recommend` — Ai Dispatch Optimize. Bearer plus resource/scope authorization.
- `POST /api/v1/ai/recommendations/merchants` — Ai Recommend Merchants. Bearer plus resource/scope authorization.
- `POST /api/v1/ai/recommendations/products` — Ai Recommend Products. Bearer plus resource/scope authorization.
- `POST /api/v1/ai/eta/predict` — Ai Eta Predict. Bearer plus resource/scope authorization.
- `GET /api/v1/ai/risk/orders/{order_id}` — Ai Order Risk. Bearer plus resource/scope authorization.
- `GET /api/v1/ai/risk/deliveries/{delivery_id}` — Ai Delivery Risk. Bearer plus resource/scope authorization.
- `GET /api/v1/ai/models` — Ai Models. Bearer plus resource/scope authorization.
- `GET /api/v1/ai/models/{model_id}/metrics` — Ai Model Metrics. Bearer plus resource/scope authorization.
- `POST /api/v1/ai/models/{model_id}/evaluate` — Ai Evaluate Model. Bearer plus resource/scope authorization.
- `GET /api/v1/ai/copilot/status` — Ai Copilot Status. Bearer plus resource/scope authorization.
- `POST /api/v1/ai/copilot/query` — Ai Copilot Query. Bearer plus resource/scope authorization.
- `PUT /api/v1/operations/cities/{city_id}/dispatch-policy` — Set Dispatch Policy. Bearer plus resource/scope authorization.
- `POST /api/v1/operations/dispatch/{task_id}/reassign` — Reassign Delivery. Bearer plus resource/scope authorization.
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
- `POST /api/v1/finance/sandbox/payments/{payment_id}/complete` — Complete Sandbox Payment. Bearer plus resource/scope authorization.
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
Total documented HTTP operations: 134.
