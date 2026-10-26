# Phase 5.A merchant operations audit

**Audit basis:** repository at Phase 5 commit `e4b700e`, plus the Phase 5.A changes in this working tree. This is a code audit, not a production deployment review.

| Area | Existing evidence | Phase 5.A outcome |
|---|---|---|
| Organization/brand/branch access | `backend/api/v1/routes.py` merchant branch endpoints and `backend/application/common.py:branch_scope` | Existing scope checks retained; new KDS endpoints check the actor's current branch permission. |
| Orders | `MerchantOrder`, `OrderItem`, order transition API and merchant queue | Existing server remains authoritative. Ready now requires all tasks completed. |
| KDS | New `KitchenStation`, `KitchenTask`, dependency records and migration `20261026_0011`; task API and merchant Flutter station board | Implemented for per-order-item prep and final packaging. Arbitrary recipes/station routing rules are not configured. |
| Inventory | `backend/application/batches.py` has row-locked FEFO allocation and consumption; inventory receipt and adjustment endpoints exist | Added branch-scoped FEFO-ordered batch listing and Flutter receipt/lot display. No recipe ingredient/BOM consumption or procurement was added. |
| Catalogue | Organization products, variants and branch prices/availability exist | No bulk import, catalogue revision publication, or global-to-branch sync workflow. |
| POS/printers | No provider configuration or hardware SDK in this repository | Vendor-neutral Python ports added. No live connector, retry queue, webhook secret store, or hardware test. |
| AI | `ai_platform/inference/service.py` exposes deterministic preparation estimates and explicit untrained/cold-start provenance | Estimate/provenance copied to kitchen tasks. No claim of trained merchant model. |
| Offline/notifications | Existing shared backend and polling screens | KDS shows connectivity/last sync and reloads server state; no offline command queue or missed-order push notification recovery. |
| Staff/analytics/procurement/transfers | No operational schema/API found for these workflows | Not delivered in this increment. |
| Flutter validation | Merchant app source exists under `apps/merchant_app` | KDS source updated; Flutter SDK is unavailable in this environment, so no build or device/tablet visual comparison is claimed. |

## Risks and boundaries

Task creation occurs within merchant acceptance and is idempotent per merchant order. Prep tasks are created from order lines and share a default Main Kitchen station; one packaging task depends on every prep task. The migration backfills accepted/preparing legacy orders with pending prep/packing tasks and labels the estimate provenance `migration_backfill`; it does not invent a target time. A task is not auto-completed by its target timestamp. Station concurrency is enforced while holding the station row lock. The current model does not support configurable routing of individual menu items to Grill/Fryer/Beverage, multi-brand shared capacity, recipe instructions, allergen data, staffing, or scheduled production batches.

The added task schema is operational data with a forward-only migration downgrade guard. Apply migrations using the normal Alembic deployment process. Do not enable the new Flutter flow against a backend until that migration has been applied.
