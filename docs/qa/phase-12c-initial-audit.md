# Phase 12.C initial audit

Date: 2026-10-27. Scope: repository inspection plus the guarded integration suite. No DB reset, production access, deployment, or default credentials were used.

## Runnable inventory

- Six app directories exist: three Next.js apps (`company_admin`, `city_operations`, `support_console`) and three Flutter apps (`customer_app`, `merchant_app`, `pilot_app`). The three Next.js roots on ports 3000–3002 returned HTTP 200 during the prior environment check. This proves only shell availability, not authenticated UI workflows.
- FastAPI source exists under `backend`. An existing API on port 8000 returned `/health/live` 200 and `/health/ready` 503 (Redis dependency unavailable). Do not interpret this running process as current source coverage.
- Local PostgreSQL is available on loopback port 5433 with `quickbuddy_dev` and isolated `quickbuddy_test`, both at migration head `20261027_0020`. The integration fixture refuses non-local/non-`quickbuddy_test` DBs and upgrades schema; it does not truncate/reset data.
- Executed `.venv\Scripts\python.exe -m pytest tests/integration -q`: **47 passed in 112.01s**.
- Redis is not available at 6379; `redis-server`/`redis-cli` were not found. Readiness, queues, websocket/realtime behavior remain blocked.
- Flutter, Dart, adb, Android SDK, and Docker were not available. Mobile runtime/integration tests are blocked.
- Project Playwright packages were absent (`node_modules/playwright` and `@playwright` checks false). Browser login and visual regression were not run.
- `quickbuddy_dev` had zero assigned users in the implemented role catalog at audit time. No static/default test accounts are configured. Integration accounts are generated per-test with random test-only identities/passwords; secrets are not recorded here. Test DB has accumulated synthetic fixtures from previous isolated tests.
- `.env.example` has Razorpay disabled with blank provider credentials. Live payment/payout behavior was not tested; sandbox payment tests are in integration suite.
- PostGIS availability was not independently verified in this Phase 12.C run; do not assume it.

## Existing role and permission source

The DB and seeded backend catalog contain 14 roles: `platform_super_admin`, `company_admin`, `country_manager`, `city_manager`, `city_operator`, `zone_manager`, `merchant_owner`, `branch_manager`, `kitchen_operator`, `delivery_fleet_manager`, `delivery_pilot`, `support_agent`, `finance_manager`, `customer`. The list in the prompt includes many titles absent from this catalog; these are identified as absent, not synthesized. See [role-permission-matrix.md](role-permission-matrix.md).

## Coverage limits

The integration suite executed 47 cases. Selected role-specific paths exist for platform admin, city manager/operator, finance manager, and support agent, plus baseline customer and pilot entities. It does **not** constitute login/dashboard/navigation testing for each of 14 roles. Flutter/browser, Redis-backed workflows, visual comparison, and broad role-action denial matrices remain NOT RUN or BLOCKED. Exact evidence is recorded in the role reports and final report.
