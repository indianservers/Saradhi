# Phase 12.B test results

Executed locally on 2026-10-27 against the isolated PostgreSQL test database.

- `.venv\\Scripts\\python.exe -m pytest backend/tests tests/unit tests/integration tests/contract -q` — **113 passed**, one Starlette/httpx deprecation warning, 100.59 seconds.
- `.venv\\Scripts\\python.exe -m pytest tests/integration/test_customer_admin_api.py -q` — **3 passed**; covers directory masking/scope, Customer 360 summary and all 11 history tabs, masked export, access denial, exact consent-aware segment count, customer-owned consent updates, verified-contact gate, idempotent replay and append-only trigger.
- `npm run typecheck --workspace=@quickbuddy/web-design-system` — passed.
- `npm run typecheck --workspace=@quickbuddy/company_admin` — passed.
- `npm run build --workspace=@quickbuddy/company_admin` — passed.
- `npm run format:check` — passed.
- `.venv\\Scripts\\python.exe -m ruff check backend tools tests` — passed.
- `tools/validation/structure.py`, `tools/validation/source_safety.py` (542 source files), and `git diff --check` — passed.
- OpenAPI export and TypeScript SDK contract generation — passed.
- Local development database migrated additively to `20261027_0020`; a fresh API process on port 8001 served the CRM, segment and consent routes in OpenAPI. The pre-existing API on port 8000 was left running and was not restarted.

No browser E2E or screenshot was captured. No high-volume dataset benchmark, XLSX/customer import, CRM AI tool, campaign sender/provider, A/B experiment, or privacy-request workflow was tested. One Starlette/httpx test-client deprecation warning remains. The test database persists between runs; integration fixtures use fresh identities and idempotency keys.
