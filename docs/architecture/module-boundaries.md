# Domain module boundaries

Each context lives in backend/modules/<name>. Empty context packages reserve ownership without
creating nonfunctional CRUD adapters. Add files only when functionality exists, following:
transport/routes.py for FastAPI adapters; application/services.py for use cases;
domain/models.py and domain/events.py for pure Python rules/events;
application/ports.py for repository protocols; infrastructure/repositories.py for ORM adapters;
tests/test_<use_case>.py for local domain tests. Domain never imports FastAPI or SQLAlchemy.
Compose dependencies at API/worker bootstraps; injection uses FastAPI Depends at the edge only.

Ownership:
- identity: principals, credentials, authentication policies and role assignments.
- organizations: organization hierarchy, staff membership, brands and tenant scope.
- geography: countries, cities, zones and service-area definitions.
- merchants: merchant types, branches, availability and merchant operations policies.
- catalog: category/product/menu definitions; inventory: stock and reservation rules.
- customers: customer profiles and addresses; carts: mutable purchasing intent.
- orders: parent checkout and child merchant order orchestration and lifecycle.
- scheduling: slots, scheduled and recurring occurrence generation.
- fulfillment: independent prep/pickup/drop-off units; dispatch: assignment decisions.
- tracking: authorized location ingestion and restricted real-time views.
- payments: payment intents/provider reconciliation; ledger: immutable balanced money postings.
- settlements: merchant/pilot payout obligations and reconciliation.
- promotions: eligibility/pricing adjustments; subscriptions: entitlements and recurrence contracts.
- notifications: template delivery/preferences; support: tickets, complaints and escalation.
- reviews: moderated customer feedback; compliance: consent, retention and regulated categories.
- analytics: read projections, reporting; ai: policy-enforced tools and inference requests.
- audit: append-only actor/action/resource records and controlled retention.

Dependency rule: shared primitives have no domain imports. Context domain code imports only its
own domain and shared immutable values. Application cross-context calls use published ports;
no context imports another's infrastructure, ORM models or tables. Avoid bidirectional
service imports; order orchestration calls independent context ports and emits events.
Read projections may join through explicitly designed adapters, never by leaking repositories.
Phase 2 must document concrete contracts before introducing cross-context implementations.

Reserved versioned events: orders.created.v1, merchants.accepted.v1, payments.confirmed.v1,
dispatch.allocated.v1, fulfillment.delivered.v1. Envelopes carry immutable ID, aggregate ID,
UTC occurred_at, version, correlation and minimal payload. TransactionalOutbox.append must
use the same PostgreSQL transaction as the state update. Consumers atomically commit effects
with unique event IDs; retry with bounded exponential backoff/jitter, durable dead-letter
storage and manual replay. Interfaces exist; reliability is not implemented or claimed.

## Phase 2 implementation layout

The reserved context packages remain ownership markers. Implemented pure invariants live in backend/domain;
application services are split into identity, commerce, batches, logistics, finance, events and maintenance.
backend/persistence contains the shared ORM registry and repositories, needed to order cross-schema FKs.
backend/api/v1 contains typed transports and dependencies. Domain code imports neither FastAPI nor ORM.
There are no circular application/context imports. Split physical context packages further as services grow;
do not duplicate models or move transaction ownership into individual frontend applications.
