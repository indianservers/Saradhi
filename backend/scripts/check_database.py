"""Read-only inspection. Never creates roles, databases, schemas or extensions."""

import asyncio
import json

from sqlalchemy import text

from backend.shared.database import create_database
from backend.shared.settings import get_settings


async def main():
    settings = get_settings()
    if "REPLACE_ME" in settings.database_url.get_secret_value():
        raise SystemExit(
            "BLOCKED: supply authorized DATABASE_URL in .env; no credentials attempted"
        )
    engine = create_database(settings)
    try:
        async with engine.connect() as conn:
            info = (await conn.execute(text("SELECT version(), current_database()"))).one()
            extensions = (
                await conn.execute(
                    text(
                        "SELECT name, installed_version FROM pg_available_extensions "
                        "WHERE name IN ('postgis', 'pgcrypto', 'pg_trgm', 'btree_gist')"
                    )
                )
            ).all()
            print(
                json.dumps(
                    {
                        "version": info[0],
                        "database": info[1],
                        "extensions": [list(row) for row in extensions],
                    }
                )
            )
    except Exception:
        raise SystemExit(
            "Database connection failed; check authorized credentials, host and grants"
        ) from None
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
