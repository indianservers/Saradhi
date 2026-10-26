# Phase 12.B final report

**Readiness: PARTIAL — not enterprise CRM complete.** See `phase-12b-feature-audit.md` for all 50 statuses. This phase adds a real, permission-scoped customer directory and read-only Customer 360 workspace over existing Quickbuddy identity, commerce, finance, engagement and support records, plus a customer-owned consent evidence ledger.

Implemented endpoints include directory, overview, orders, payments/refunds, address summaries, subscriptions, loyalty, referrals, coupon history, support tickets, feedback, privacy preferences and consent evidence, security events/session count, bounded masked customer CSV export, and a typed, audited, city-scoped segment count preview. The Company Admin UI exposes a searchable directory, selected-profile summary, lazy-loaded tabs and a small segment preview form. Migration `20261027_0019` grants `customer.read` to selected admin roles; scope filters non-global directory/order reads by authorized order organizations/cities. Migration `20261027_0020` adds append-only self-service marketing consent events; it does not authorize or send campaigns.

The directory/export are intentionally limited to 50/500 rows respectively, mask email and phone, and omit precise addresses, payment references and review bodies. Order totals are gross historical purchases; they are not customer profitability or CLV. Customer import, saved/scheduled segments, RFM/cohorts, campaigns, experiments, privacy request processing, CRM AI and Flutter UI changes remain absent. No customer identities were created or modified by an import. No external messaging or payment action was performed.

See `phase-12b-test-results.md` for automated evidence and limitations. The Phase 12.A branch import/export work remains part of the current uncommitted change set; no deployment or commit was requested.

## Local startup

From the repository root in PowerShell, use the existing local PostgreSQL cluster and migrate through `20261027_0020` before starting the API. Then run the Company Admin frontend in a separate terminal:

```powershell
./tools/local-postgres.ps1 status
./tools/local-postgres.ps1 start  # only if this project's cluster is stopped
./tools/dev.ps1 database
./tools/dev.ps1 migrate
./tools/dev.ps1 api
./tools/dev.ps1 web -App company_admin
```

The workspace screen is served at `/workspace`; the CRM is a tab within Company Admin rather than a separate `/customers/[customerId]` route. A local admin identity needs a current database-backed `customer.read` assignment from migration `20261027_0019`; global platform administrators can view all cities, while scoped assignments are filtered through permitted order cities/organizations. Customer-authored consent events use `/api/v1/me/consents` after migration `20261027_0020`.
