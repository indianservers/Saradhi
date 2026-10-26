# Phase 9 test results

This file records results after the Phase 9 gateway and agent API implementation. Run the commands below from the repository root:

```powershell
.venv\Scripts\python.exe -m ruff check ai_platform backend
.venv\Scripts\python.exe -m pytest backend/tests/test_ai_gateway.py tests/unit/test_ai_baselines.py -q
.venv\Scripts\python.exe -m pytest tests/integration/test_reliability.py -q
npm run contracts
npm run typecheck --workspaces --if-present
```

The real PostgreSQL suite is opt-in and skips unless `TEST_DATABASE_URL` points to the isolated local `quickbuddy_test` database. Provider integration was exercised only with an HTTP mock; no external model credentials or service were used. Flutter/Dart availability must be checked before claiming Flutter analysis/build results.

## Verified run: 2026-10-27

- Full backend, unit, integration and contract suite: **93 passed**, one Starlette/httpx deprecation warning (94.41 seconds).
- Shared-gateway and forecasting unit tests: **9 passed**.
- Role-scoped agent integration: **1 passed**, including a real catalog price/stock response and denied cross-city access.
- Ruff checks on changed Python files: passed.
- OpenAPI export and TypeScript contract generation: passed.
- Workspace TypeScript checks: passed.
- Flutter and Dart executables are not installed; native customer/merchant/pilot UI builds were not run.
- No live provider request, trained model evaluation or production performance benchmark was run.
