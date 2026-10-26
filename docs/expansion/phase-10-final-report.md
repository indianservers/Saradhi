# Phase 10 implementation report

## Implemented slice

- Migration `20261027_0017` adds explicit `active`/`paused`/`cancelled` recurring-plan lifecycle state and is applied to local dev/test databases.
- New city records start inactive. Readiness and authorized activation/suspension APIs validate zone/category plus an approved pickup-capable merchant, inventory, price and future capacity. City transitions are audited. Public city/catalog/branch discovery filters inactive cities.
- Admins can configure non-regulated categories per inactive zone. Regulated/pharmacy categories remain blocked from enablement and checkout.
- Customer recurring schedules can be created from an owned open cart, listed, paused/resumed/cancelled and skipped. A durable ARQ job materializes review-required occurrences with a uniqueness key and scheduling-job row. No recurring order/payment is submitted without revalidation and ordinary customer checkout.
- Existing common parent/child order, inventory/price, serviceability, forecasting and finance models remain the authoritative engines.

Key API paths added or changed: `POST /geo/cities` creates a draft; `GET /operations/cities/{city_id}/readiness`; `POST /operations/cities/{city_id}/activate|suspend`; `PUT /geo/zones/{zone_id}/categories`; and `POST|GET /fulfillment/recurring-plans`, `PUT /fulfillment/recurring-plans/{plan_id}/status`, `POST .../{plan_id}/skip`, `GET .../{plan_id}/occurrences`.

## Not complete

There is no full admin launch wizard, city boundary/policy editor, grocery substitution/weight workflow, pharmacy workflow, retail return flow, parcel order flow, subscription benefit/billing integration, corporate ordering, bulk import, partner logistics API, ONDC adapter, hierarchical feature flag service, complete COD/settlement reconciliation, or six-app category UI. PostGIS remains a deployment prerequisite for delivery geofencing; no production integration credentials were supplied. No 10,000/day performance claim is made.

See `phase-10-audit.md` and `phase-10-test-results.md` for feature status and exact local verification commands.
