# Phase 10 capability audit

Repository audit performed on 2026-10-27. Earlier implementation changes are already present in the shared working tree and were left intact. This audit distinguishes deployed service behavior from schema-only foundations and external integration readiness.

| Area | Classification | Current evidence / limitation |
|---|---|---|
| Country/city/zone hierarchy | Implemented, activation incomplete | Country, city and zone CRUD exist. City create defaults `active=true`; no launch wizard, readiness validation, version history or approval lifecycle. |
| Category registry | Partial | Shared category table, regulated bit, category attributes and zone/category availability exist. No versioned typed capability registry or policy activation workflow. |
| Serviceability | Partial, production blocked | Checkout revalidates branch, zone/category, operating calendar, method, capacity and optional PostGIS geometry. It returns 503 when the spatial extension/boundary migration is unavailable; delivery uses no straight-line substitute. Dynamic restrictions and cross-zone travel are absent. |
| Merchant hierarchy/onboarding | Implemented core | Organizations, brands, branches, review decisions, KYC/document/contract schema exist. Bulk import and city launch onboarding workflow are absent. |
| Shared catalogue/food commerce | Implemented core, incomplete | Shared product/variant/price/stock, options and kitchen task foundations exist. Customized option pricing, configured tax, and variable weight explicitly block checkout. |
| Grocery | Partial | Shared stock and pick/pack foundations exist. No batch/expiry, substitution consent, variable-weight authorization adjustment or complete missing-item workflow. |
| Pharmacy | Restricted/blocked | `regulated` categories are explicitly rejected during checkout. No prescription upload/pharmacist workflow. Keep disabled. |
| Retail | Partial | Shared products and variants are usable; image/specification/return/exchange workflows are incomplete. |
| Parcel | Missing workflow | Brand merchant type includes parcel, but no parcel quote/request/proof lifecycle exists. |
| Multi-merchant cart/orders | Implemented core | Shared cart, one-currency quote, parent order and merchant child allocations exist. Different currencies are rejected; delivery-slot/address grouping and richer category compatibility are limited. |
| Scheduling | Partial | Merchant delivery windows, city calendars/holidays and capacity exist. No multiple-slot atomic checkout workflow or recurring worker. |
| Recurring orders | Schema + helper only before this phase | Plans/rules/exceptions/occurrences and DST-aware occurrence calculation exist. No customer plan APIs, durable worker, or payment/order execution. Phase 10 adds safe plan management and idempotent review-only occurrence materialization. |
| Subscriptions | Schema only | Plan, customer subscription and billing-event tables exist. No plan eligibility/benefit ledger, renewal service or payment authorization. Razorpay subscription billing remains unavailable. |
| Corporate/B2B | Missing | No corporate approval/budget/order context. |
| Bulk onboarding | Missing | No controlled CSV/XLSX parser, dry run or import audit flow. |
| Partner logistics API | Schema-only integration base | Partner credentials/webhook subscription/inbox tables exist; no scoped public quote/create/tracking contract. |
| POS/ERP connectors | Contract stubs only | POS/integration package exists, but no credentialed live connector, sync checkpoints or verified partner connectivity. |
| ONDC | Missing / blocked | No protocol adapter or onboarding; no production access. |
| Pricing/finance | Partial | Quote snapshots and finance/ledger foundations exist. Taxes and several pricing components intentionally block checkout; COD, complete refunds and settlements are not complete. |
| Multi-city AI | Partial deterministic | Point-in-time demand baseline, city/zone forecast and scoped dispatch advisory exist. No trained model, category-specific forecast or profitability model. |
| Feature flags | Missing | No server-enforced hierarchical rollout service. |
| Load evidence | Insufficient for target | Existing local smoke tests are functional, not 10,000-orders/day capacity evidence. No representative expansion benchmark. |

## Phase 10 implementation boundary

The recurring-plan APIs added in this phase create schedules from a customer's own open cart, support pause/resume/cancel/skip, and materialize occurrences with a uniqueness key. Generated occurrences wait for price, stock, slot, merchant and payment revalidation and customer checkout. No recurring charge or order is automatic. The other incomplete/high-risk capabilities above remain documented production blockers rather than being represented as complete.
