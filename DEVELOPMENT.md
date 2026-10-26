# Local development

Run commands in PowerShell from the monorepo root. All dependency installs stay local.
No global software installation or service modification is performed by these scripts.

```powershell
./tools/dev.ps1 verify
Copy-Item .env.example .env # once only; preserve an existing .env
./tools/dev.ps1 install
./tools/dev.ps1 infra       # Redis only; requires Docker
./tools/dev.ps1 api         # terminal 1, localhost:8000
./tools/dev.ps1 web -App company_admin   # terminal 2, localhost:3000
./tools/dev.ps1 web -App city_operations # localhost:3001
./tools/dev.ps1 web -App support_console # localhost:3002
./tools/dev.ps1 worker      # separate terminal; requires Redis
```

An existing Redis can replace Docker by setting REDIS_URL. PostgreSQL is the existing host
installation; no replacement server is included. Supply authorized credentials for
quickbuddy_dev in .env before running `./tools/dev.ps1 database`. Do not reuse another
project's database, inspect its secrets or guess a password. See database/scripts/README.md.

```powershell
./tools/dev.ps1 contracts
./tools/dev.ps1 test
./tools/dev.ps1 lint
./tools/dev.ps1 format
npm run build
./tools/dev.ps1 worker-smoke
./tools/dev.ps1 worker-health
```

Worker health requires an active worker; smoke enqueues and runs one harmless demonstration.
It requires a real Redis. No mock is reported as a Redis integration pass.

Flutter SDK/Android SDK must be installed explicitly by the developer. No system-wide install
is attempted. Once available:

```powershell
./tools/dev.ps1 flutter-init -App customer_app
./tools/dev.ps1 flutter-init -App pilot_app
./tools/dev.ps1 flutter-init -App merchant_app
./tools/dev.ps1 mobile -App customer_app # web port 8080
./tools/dev.ps1 mobile -App pilot_app    # web port 8081
./tools/dev.ps1 mobile -App merchant_app # web port 8082
```

Flutter initialization creates missing Android/iOS/web runners using flutter create in a
staging directory. It never overwrites app source. Flutter web builds are `flutter build web`
inside each app. Android emulator API address is http://10.0.2.2:8000; physical devices need
an explicitly configured host. iOS compilation requires macOS/Xcode. Android requires
Android SDK/licenses. Release app identifiers/signing and secure storage setup remain release gates.

The .env at repository root is read by Python. Each web app reads its own .env.local
(API_BASE_URL, server-only). Flutter uses compile-time --dart-define values. Never put secrets
in NEXT_PUBLIC variables or dart defines. Access tokens must never enter browser localStorage.

Docker full profile is optional: set DOCKER_DATABASE_URL with host.docker.internal and authorized
quickbuddy_dev credentials, then `docker compose --profile full up --build`. The host PostgreSQL
must explicitly permit the container client; this project does not change host authentication.
Containers use Redis on the internal Compose network. Shut down via `docker compose down`;
add no -v unless explicitly choosing to discard demo Redis state.

Unix: python3 -m venv .venv; .venv/bin/pip install -r requirements.lock; npm ci.
Use .venv/bin/python -m uvicorn backend.api.app.main:app --no-access-log and the same npm scripts.
