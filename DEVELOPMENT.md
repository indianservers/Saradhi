# Local development — Phase 2

Run PowerShell commands from the monorepo root. Python dependencies are project-local in .venv
and Node dependencies in npm workspaces. No global installation or cloud provisioning occurs.

```powershell
./tools/local-postgres.ps1 status
./tools/local-postgres.ps1 start  # only if the isolated project cluster is stopped
./tools/dev.ps1 database
./tools/dev.ps1 migrate
./tools/dev.ps1 migrate-test
./tools/dev.ps1 api
```

The approved isolated cluster reuses the detected PostgreSQL 17.11 binaries and stores data
inside .local/postgres-data on 127.0.0.1:5433. tools/local-postgres.ps1 reads the detected binary
path from ignored .local/postgres-toolchain.json. It never changes the unrelated 5432 server.
`stop` stops only this project's data directory. .env already contains generated separate
DATABASE_URL/TEST_DATABASE_URL and AUTH_PRIVATE_KEY_PATH; do not overwrite it with the example.
The local owners are not superusers and cannot create roles/databases. No default user exists.

API: http://127.0.0.1:8000; Swagger: /docs; OpenAPI: /openapi.json. Liveness checks the process;
readiness also checks PostgreSQL and Redis. Redis is missing, so readiness remains 503 while
PostgreSQL and database-backed APIs work. The PostgreSQL worker does not need Redis:

```powershell
./.venv/Scripts/python.exe -m backend.workers.database_worker --once
# Omit --once to poll persisted due state; no in-memory business scheduling authority.
./tools/dev.ps1 integration
./tools/dev.ps1 test
./tools/dev.ps1 lint
./tools/dev.ps1 contracts
./.venv/Scripts/python.exe tools/generators/schema_artifacts.py
./.venv/Scripts/python.exe tools/generators/api_reference.py
./.venv/Scripts/python.exe -m backend.scripts.database_report
```

Integration tests use only local quickbuddy_test, migrate it without resetting it and keep
uniquely named test fixtures/history. They never drop/truncate dev or test databases. The suite
includes 100 independently authenticated concurrent checkouts. If TEST_DATABASE_URL is missing,
the integration suite explicitly skips; missing infrastructure is never reported as passing.
CI has an ephemeral PostgreSQL service and executes the same real integration suite.

Registration/login examples are in docs/api/sample-requests.ps1. To provision platform access
for an actual named local user after registering it, explicitly run:
`./.venv/Scripts/python.exe -m backend.scripts.grant_platform_admin --user-id <existing-user-uuid>`.
This local operator command creates no password and records the grant. Do not grant arbitrary
users access. Merchant self-onboarding receives only its own merchant-owner scope. Review and
finance permissions still require authorized, separate actors.

For a NEW checkout on another machine, install dependencies with `./tools/dev.ps1 install`,
configure authorized dedicated local URLs in ignored .env, generate a development signing key
with `python -m backend.scripts.init_auth`, then migrate. Local bootstrap scripts for the isolated
cluster deliberately refuse to replace existing credentials/databases. Never blindly rerun initdb
or overwrite .env. Keep keys/connection credentials private; production uses external secret storage.

Web apps remain independently runnable (separate terminals):

```powershell
./tools/dev.ps1 web -App company_admin     # 3000
./tools/dev.ps1 web -App city_operations   # 3001
./tools/dev.ps1 web -App support_console   # 3002
npm run build
```

No frontend screens changed in Phase 2. API_BASE_URL is each web app's server-side .env.local
configuration. The guarded workspace checks /api/v1/me; a proper HttpOnly/Secure callback must
be wired before browser sign-in. Do not persist tokens in localStorage or NEXT_PUBLIC values.

Flutter/Dart/Android tools remain unavailable. Once explicitly installed, use:
`./tools/dev.ps1 flutter-init -App customer_app` (repeat for pilot_app/merchant_app), then
`./tools/dev.ps1 mobile -App customer_app` (ports 8080/8081/8082 respectively).
Each app README describes build/test commands and Android emulator API address 10.0.2.2.
Dart contract toolchain is documented in packages/api_contracts/README.md; it was not run locally.

Docker/Redis are still unavailable. If explicitly installed later, `./tools/dev.ps1 infra`
starts Redis only. ARQ demonstration commands remain worker/worker-smoke/worker-health.
The optional full Compose profile needs a separate DOCKER_DATABASE_URL using host.docker.internal;
the host PostgreSQL authentication must explicitly permit the client. Compose/PostGIS paths have
not been validated here and do not silently alter database service configuration.

PostGIS: read docs/database/postgis-requirements.md. Until the compatible extension, reviewed
migration, real service polygons and policy tests exist, courier serviceability correctly fails.
Sandbox payments are disabled in .env; only automated test settings explicitly enable the
non-network deterministic adapter. No production charge/payout/provider SMS is performed.
