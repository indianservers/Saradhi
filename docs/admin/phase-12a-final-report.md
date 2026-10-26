# Phase 12.A final report

**Readiness: PARTIAL — not an enterprise-admin launch.** The 50-feature audit records **0 verified end-to-end, 36 partial, 10 missing and 4 blocked** based on evidence in this repository. Only a guarded first P0 slice was implemented: branch CSV import/export and Company Admin Data Operations.

## Delivered

- A private `admin` schema migration with bulk job, row and external-reference records; current Alembic head is `20261027_0018`.
- Bounded CSV upload, safe field mapping, validation/dry-run, per-row scoped authorization, actor-owned job status/errors, idempotent commit, and cancellation of validated uncommitted jobs.
- Branch creation routes through the existing merchant domain model and always leaves branches pending and closed for separate review.
- Scoped, audited on-demand branch CSV export with formula escaping and no public or persisted export files.
- Company Admin Data Operations screen, branch template, mapping/preview/commit/cancel flow, job history and selected-city export.
- OpenAPI and generated TypeScript SDK updates, architecture notes and a 50-feature evidence matrix.

## Verification

`docs/admin/phase-12a-test-results.md` records exact commands and results: 110 tests passed; the focused PostgreSQL bulk API tests passed 2/2; Company Admin typechecks/build, formatting, Ruff, structure and source-safety checks passed. No high-volume performance benchmark or browser E2E evidence is claimed.

## Remaining limits

Imports support branches only, CSV only, at most 5 MiB/5,000 uploaded rows, and synchronous commit of at most 200 eligible rows. New branches remain pending and closed. There are no XLSX imports, async workers/resumable chunks, persisted export center/private object storage, customer/pilot/catalogue/price/stock imports, customer or merchant 360 APIs, campaign provider, report builder, or bulk approvals. The other 49 gap items remain at their audited status. Apply migration `20261027_0018` through the reviewed release process; no deployment or production migration was performed.
