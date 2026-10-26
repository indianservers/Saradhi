# Phase 10 test results

Run from the repository root:

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m pytest backend/tests tests/unit tests/integration tests/contract -q
.venv\Scripts\python.exe -m ruff check backend
npm run contracts
npm run typecheck --workspaces --if-present
```

The integration fixture refuses databases outside local `quickbuddy_test` and upgrades that isolated test DB before tests. New cases cover city activation readiness, hiding inactive city catalogue, regulated-category rejection, recurring plan owner scope, pause/skip, unique occurrence materialization and no automatic order/charge. Local performance/scalability and third-party connectivity are not inferred from functional tests.

## Verified run: 2026-10-27

- Full backend, unit, integration and contract suite: **95 passed**, one Starlette/httpx deprecation warning (95.78 seconds).
- Focused city activation, recurring schedule, recurrence dedupe, AI baseline and city authorization scenarios: **5 passed**.
- Full backend Ruff checks: passed.
- OpenAPI export and TypeScript client generation: passed.
- Workspace TypeScript checks: passed.
- Migration 20261027_0017 applied to the guarded local `quickbuddy_dev`; the integration fixture upgraded guarded `quickbuddy_test` to the same head.
- Flutter/Dart are not installed; no Flutter application builds were run.
- No production-load, 10,000-orders/day, external POS, ONDC, partner API or real payment provider measurement was made.
- After that full run, recurring lifecycle, cancellation terminal-state and occurrence dedupe scenarios passed in focused integration reruns (**2 passed**).
