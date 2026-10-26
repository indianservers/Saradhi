# Local development (Windows)

Run from `C:\Indian Servers\Quickbuddy`; preserve the existing PostgreSQL data. First run `tools\verify-environment.ps1`. It only detects installed tools. Copy `.env.example` to untracked `.env` and set the existing local DB credentials.

- API: `.venv\Scripts\python.exe -m uvicorn backend.api.app.main:app --reload --host 127.0.0.1 --port 8000`
- Worker: `.venv\Scripts\python.exe -m arq backend.workers.main.WorkerSettings`
- Redis container only: `docker compose up -d redis`; stop with `docker compose stop redis` (persistent volume remains).
- API and worker containers: `docker compose --profile full up --build`; `docker compose --profile full down` stops containers but retains named volumes. Confirm `DATABASE_URL` points to the intended local DB before starting. Compose does not include PostgreSQL.
- Web workspaces: `npm run dev --workspace=@quickbuddy/company-admin`, `npm run dev --workspace=@quickbuddy/city-operations`, `npm run dev --workspace=@quickbuddy/support-console`; stop each with Ctrl+C.
- Web validation: `npm run typecheck --workspaces --if-present`, `npm run build --workspaces --if-present`.
- Flutter (when installed): `cd apps\customer_app; flutter pub get; flutter run`; repeat for `apps\delivery_pilot_app` and `apps\merchant_app`. Stop with Ctrl+C. Flutter is currently absent here.
- Migrations: `.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head`; inspect `current`/`heads` first. Never reset/drop the local DB.
- Backend checks: `.venv\Scripts\python.exe -m pytest`; lint: `.venv\Scripts\ruff.exe check backend tools tests`.
- Health: `Invoke-RestMethod http://127.0.0.1:8000/health/live`; readiness: `/health/ready`.

Do not stop or kill arbitrary processes by port. Stop only terminals/services you started.
