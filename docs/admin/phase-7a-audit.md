# Phase 7.A implementation audit

Reviewed the three Next.js admin apps, shared `AdminControlTower`, backend v1 routes, permission and scope checks, migrations through `20261026_0015`, tests, and local capability health.

## Implemented in this pass

- Organization-specific finance approval list guarded by `finance.read`, ordered and cursor paginated.
- Authorized organization picker only includes active organization memberships with a `finance.read` assignment; platform super admins receive the organizations list.
- Finance UI approve/reject actions use the existing maker-checker decision endpoint, require a reason, and refresh the queue after success.
- Proxy allowlist restricts the new reads and decision writes to the exact finance route patterns; backend remains authoritative.
- Integration test proves visibility is scoped and an unrelated user cannot read the queue.

## Current admin surface

The company console has live city dispatch aggregates, verified fleet state counts, pilot incident lifecycle actions, approved branches, model registry, and finance refund approvals. City operations has city scoped dispatch and incidents. Support has claim, conversation, reply, and resolve workflows. All data comes from backend reads; the shared hook refreshes snapshots every 30 seconds.

## Unimplemented or infrastructure blocked

No cross-city map/GPS roster, manual dispatch reassignment, merchant application review queue, pilot KYC roster, customer/order command center, finance ledger reporting, alert ownership/escalation engine, staff administration, internal-only support notes, arbitrary global search, or functioning AI copilot endpoint exists in the current backend contract. Cross-instance WebSockets are disabled because Redis is unavailable locally. These are not represented with sample data.

## Required verification limits

Browser session has no test credentials. Protected authenticated pages cannot be visually verified by automating login. Performance measurements and production service reliability are not claimed.
