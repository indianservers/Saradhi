# Phase 12.A test results

Executed in the local checkout on 2026-10-27. PostgreSQL integration tests used the isolated `quickbuddy_test` database and Alembic migration path.

## Results

- `.venv\\Scripts\\python.exe -m pytest backend/tests tests/unit tests/integration tests/contract -q` — **110 passed**, one Starlette/httpx deprecation warning, 166.49 seconds.
- `backend/tests/test_bulk_data.py` — parser and mapping unit coverage; included in the full suite.
- `tests/integration/test_bulk_data_api.py` — **2 passed** in focused PostgreSQL run; covers branch import preview/commit, repeat idempotency, pending/closed state, job ownership, scoped export and denied access.
- `npm run typecheck --workspace=@quickbuddy/web_design_system` — passed.
- `npm run typecheck --workspace=@quickbuddy/company_admin` — passed.
- `npm run build --workspace=@quickbuddy/company_admin` — passed.
- `npm run format:check` — passed after formatting the Company Admin changes.
- `.venv\\Scripts\\python.exe -m ruff check backend tools tests` — passed.
- `tools/validation/structure.py` and `tools/validation/source_safety.py` — passed. The latter checks 525 source files for selected key-material patterns and import hygiene; it is not a comprehensive secret scan.
- `git diff --check` — passed.

## Coverage limits

There is no high-volume import benchmark, browser E2E run, async worker/recovery test, XLSX coverage or proof of all 50 enterprise workflows. The backend integration suite validates a local isolated PostgreSQL database; no production database was accessed. One deprecation warning remains from the installed Starlette/httpx test client combination.
