"""Read-only catalog and EXPLAIN evidence. Never prints connection strings or row PII."""

import asyncio
import json
import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import text

from backend.persistence.registry import metadata
from backend.shared.database import create_database
from backend.shared.settings import Settings

SCHEMAS = [
    "identity",
    "geo",
    "merchant",
    "catalog",
    "inventory",
    "commerce",
    "fulfillment",
    "finance",
    "engagement",
    "operations",
    "intelligence",
    "integration",
    "audit",
]


async def inspect(url, environment):
    settings = Settings(_env_file=None, app_env=environment, database_url=url)
    engine = create_database(settings)
    try:
        async with engine.connect() as db:
            result = {
                "database": await db.scalar(text("SELECT current_database()")),
                "server": await db.scalar(text("SHOW server_version")),
                "migration": await db.scalar(text("SELECT version_num FROM alembic_version")),
                "current_user_is_superuser": await db.scalar(
                    text("SELECT rolsuper FROM pg_roles WHERE rolname=current_user")
                ),
            }
            for label, sql in {
                "tables": (
                    "SELECT count(*) FROM pg_class c JOIN pg_namespace n "
                    "ON n.oid=c.relnamespace WHERE n.nspname=ANY(:schemas) AND c.relkind='r'"
                ),
                "constraints": (
                    "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n "
                    "ON n.oid=c.connamespace WHERE n.nspname=ANY(:schemas)"
                ),
                "indexes_including_constraint_indexes": (
                    "SELECT count(*) FROM pg_indexes WHERE schemaname=ANY(:schemas)"
                ),
                "triggers": (
                    "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
                    "JOIN pg_namespace n ON n.oid=c.relnamespace "
                    "WHERE NOT t.tgisinternal AND n.nspname=ANY(:schemas)"
                ),
            }.items():
                result[label] = await db.scalar(text(sql), {"schemas": SCHEMAS})
            rows = (
                await db.execute(
                    text("""SELECT n.nspname,t.relname,count(*) AS count
                FROM pg_constraint k JOIN pg_class t ON t.oid=k.conrelid
                JOIN pg_namespace n ON n.oid=t.relnamespace
                WHERE n.nspname=ANY(:schemas) AND k.contype<>'t'
                GROUP BY n.nspname,t.relname"""),
                    {"schemas": SCHEMAS},
                )
            ).all()
            result["constraint_count_differences"] = {}
            for schema, name, count in rows:
                table = metadata.tables.get(schema + "." + name)
                if table is not None and count != len(table.constraints):
                    names = (
                        await db.execute(
                            text("""SELECT conname,contype::text FROM pg_constraint
                        WHERE conrelid=CAST(:name AS regclass)"""),
                            {"name": schema + "." + name},
                        )
                    ).all()
                    result["constraint_count_differences"][schema + "." + name] = {
                        "database": count,
                        "model": len(table.constraints),
                        "names": [list(row) for row in names],
                    }
            result["extension_availability"] = [
                dict(row._mapping)
                for row in (
                    await db.execute(
                        text(
                            "SELECT name,installed_version FROM pg_available_extensions "
                            "WHERE name IN ('postgis','pgcrypto','pg_trgm','btree_gist') "
                            "ORDER BY name"
                        )
                    )
                ).all()
            ]
            if environment == "test":
                result["plans"] = {}
                queries = {
                    "owned_order_page": (
                        "SELECT id,status FROM commerce.orders WHERE user_id="
                        "(SELECT user_id FROM commerce.orders LIMIT 1) ORDER BY id LIMIT 51"
                    ),
                    "stock_lookup": (
                        "SELECT id,on_hand,reserved FROM inventory.stock_balances "
                        "WHERE branch_id=(SELECT branch_id FROM inventory.stock_balances LIMIT 1) "
                        "ORDER BY id LIMIT 51"
                    ),
                    "latest_pilot_location": (
                        "SELECT latitude,longitude FROM fulfillment.pilot_latest_location "
                        "WHERE pilot_id=(SELECT id FROM fulfillment.pilot_profiles LIMIT 1)"
                    ),
                    "outbox_due": (
                        "SELECT id FROM integration.outbox_events WHERE delivered_at IS NULL "
                        "AND dead_lettered_at IS NULL AND available_at<=now() "
                        "ORDER BY available_at LIMIT 50"
                    ),
                }
                for name, query in queries.items():
                    plan = await db.scalar(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query))
                    result["plans"][name] = plan
            result["pool"] = engine.pool.status()
            return result
    finally:
        await engine.dispose()


async def main():
    config = dotenv_values(".env")
    report = {}
    for name, key in [("development", "DATABASE_URL"), ("test", "TEST_DATABASE_URL")]:
        url = os.environ.get(key) or config.get(key)
        if not url or "REPLACE_ME" in url:
            continue
        report[name] = await inspect(url, name)
    target = Path("docs/operations/phase-2-database-evidence.json")
    target.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    for name, value in report.items():
        print(
            name,
            {
                key: item
                for key, item in value.items()
                if key not in {"plans", "extension_availability", "pool"}
            },
        )
    print(target)


if __name__ == "__main__":
    asyncio.run(main())
