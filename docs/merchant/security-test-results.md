# Merchant security test results

Date: 2026-10-26. Controlled local integration records only.

The new integration test verifies: authorized branch list includes the merchant’s branch only; the same account receives `403` for another merchant’s queue and catalogue; the queue contains the real child-order line snapshot; an authorized merchant can accept a pending order; and a stale expected version is rejected with `409`. Existing branch-scoped inventory authorization tests also deny cross-organization access. Exact current counts are in `phase-5-final-report.md`.

The new branch-list query checks active membership, active user, current `merchant.write` role permission, and assignment organization/city/branch constraints. Queue/catalog/availability/transitions repeat backend scope checks. Client branch selection is navigation state only. Auth tokens are stored with shared platform secure storage; logout clears tokens. No banking/KYC data is collected by the app.

Not covered: Flutter/device secure storage inspection, refresh rotation on app restart, KYC upload isolation, finance-viewer permissions, WebSocket tenant isolation, push de-duplication, staff role management, concurrent human UI acceptance, production logs, app background behavior or gateway. Backend state transitions are row/version guarded, but no two-device merchant concurrency test was run here. This is not a security certification.
