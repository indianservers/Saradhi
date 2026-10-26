# Windows local setup

Canonical commands: ../../DEVELOPMENT.md. API on 127.0.0.1:8000; web on 3000/3001/3002;
Flutter web on 8080/8081/8082. CORS explicitly lists these browser origins. Use the host
PostgreSQL; docker compose provides Redis only by default. No database data volume is created.

Detected PostgreSQL listener belongs to postgres.exe bundled under another project's directory;
there is no PostgreSQL Windows service discovered. Its client reports 17.11 but server version
requires authenticated SQL and is not inferred from the client. Do not modify its service,
cluster, auth configuration, credentials or project database. Database owner must approve
creating a dedicated quickbuddy_dev and role. Check script is read-only and refuses the sample
credential placeholder. No connection attempt was made using guessed or unrelated credentials.

Readiness returns 503 while dependencies are unavailable; liveness remains 200. API can boot
without infrastructure so contract generation and isolated tests work. Docker and Flutter are
optional for Python/web work but required to validate the relevant pending integration paths.
