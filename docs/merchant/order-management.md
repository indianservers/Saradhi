# Merchant order management

## Live order data

`GET /api/v1/merchant/branches/{branch_id}/orders` checks the logged-in user’s branch permission, pages merchant child orders and returns the line item snapshot needed for the queue. It excludes customer names and private addresses. The Flutter dashboard/orders/KDS poll this endpoint every 15/12/10 seconds respectively, provide retry/empty states and never accept an order offline.

## Allowed workflow

The details screen submits `POST /api/v1/merchant-orders/{child_id}/transition` with the current expected version for pending → accepted → preparing → ready. Backend commerce rules, row locks, reservation validation, stock consumption/release, history, audit/outbox behavior remain authoritative. Stale versions are surfaced and the queue reloads. No local-only status change is made.

Reject reason is not collected because the transition contract has no reason field; customer notes/modifiers are also not returned. Mark-ready does not pretend to confirm pilot pickup. Fulfillment polling/handover UI, adjustable preparation estimates, station-level item progress, push notifications and WebSocket subscriptions are not implemented. Queue polling is a resilience baseline, not a prompt real-time or background-notification guarantee.
