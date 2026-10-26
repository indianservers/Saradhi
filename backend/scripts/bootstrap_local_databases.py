"""Create ONLY missing named databases in the user-approved isolated 5433 cluster.

No reset/drop, no credentials printed, no access to the unrelated 5432 cluster.
Initial admin password must already have been produced for this project's initdb.
"""

import asyncio
import secrets
from pathlib import Path

import asyncpg


async def main():
    root = Path.cwd()
    if (root / ".env").exists():
        raise SystemExit("Refusing to overwrite .env; configure existing credentials explicitly")
    password = (root / ".secrets/postgres-init-password.txt").read_text(encoding="ascii")
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="quickbuddy_local_admin",
        password=password,
        database="postgres",
    )
    credentials = {}
    try:
        for database in ("quickbuddy_dev", "quickbuddy_test"):
            role = database + "_owner"
            if await connection.fetchval("SELECT 1 FROM pg_roles WHERE rolname=$1", role):
                raise SystemExit("Dedicated owner already exists; refusing credential replacement")
            if await connection.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", database):
                raise SystemExit("Named database already exists; refusing overwrite")
            secret = secrets.token_urlsafe(48)
            # Identifiers are fixed above and password is generated URL-safe, never caller SQL.
            await connection.execute(
                f"CREATE ROLE {role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '{secret}'"
            )
            await connection.execute(f"CREATE DATABASE {database} OWNER {role}")
            await connection.execute(f"REVOKE ALL ON DATABASE {database} FROM PUBLIC")
            credentials[database] = (
                f"postgresql+asyncpg://{role}:{secret}@127.0.0.1:5433/{database}"
            )
        target = root / ".env"
        target.write_text(
            "APP_ENV=development\nDATABASE_URL="
            + credentials["quickbuddy_dev"]
            + "\nTEST_DATABASE_URL="
            + credentials["quickbuddy_test"]
            + "\nAUTH_PRIVATE_KEY_PATH=.secrets/access-private.pem\nREDIS_URL=redis://127.0.0.1:6379/0\n",
            encoding="utf-8",
        )
        target.chmod(0o600)
        print("Created quickbuddy_dev and quickbuddy_test on the approved isolated 5433 cluster.")
        print("Dedicated non-superuser owner URLs saved to ignored .env. No credentials printed.")
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
