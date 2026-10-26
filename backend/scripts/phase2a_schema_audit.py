"""Read-only model/catalog comparison for the local Quickbuddy databases."""

import asyncio
import json
import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import inspect
from sqlalchemy.engine import make_url

from backend.persistence.registry import metadata
from backend.shared.database import create_database
from backend.shared.settings import Settings

SCHEMAS = (
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
)


async def audit(database_url: str, expected: str) -> dict:
    url = make_url(database_url)
    if url.database != expected or url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit(f"Refusing schema audit outside local {expected}")
    engine = create_database(Settings(_env_file=None, app_env="test", database_url=database_url))
    try:
        async with engine.connect() as connection:

            def inspect_schema(sync_connection):
                inspector = inspect(sync_connection)
                model_tables = {
                    key for key, table in metadata.tables.items() if table.schema in SCHEMAS
                }
                database_tables = {
                    f"{schema}.{name}"
                    for schema in SCHEMAS
                    for name in inspector.get_table_names(schema=schema)
                }
                missing = sorted(model_tables - database_tables)
                extra = sorted(database_tables - model_tables)
                missing_columns, extra_columns, timezone_issues = [], [], []
                model_column_count = database_column_count = 0
                for key in sorted(model_tables & database_tables):
                    table = metadata.tables[key]
                    db_columns = {
                        col["name"]: col
                        for col in inspector.get_columns(table.name, schema=table.schema)
                    }
                    model_columns = {col.name: col for col in table.columns}
                    model_column_count += len(model_columns)
                    database_column_count += len(db_columns)
                    missing_columns.extend(
                        f"{key}.{name}" for name in model_columns.keys() - db_columns.keys()
                    )
                    extra_columns.extend(
                        f"{key}.{name}" for name in db_columns.keys() - model_columns.keys()
                    )
                    for name in model_columns.keys() & db_columns.keys():
                        model_type, db_type = model_columns[name].type, db_columns[name]["type"]
                        if getattr(model_type, "timezone", None) and not getattr(
                            db_type, "timezone", False
                        ):
                            timezone_issues.append(f"{key}.{name}")
                invalid_constraints = []
                for key in sorted(database_tables):
                    schema, table = key.split(".", 1)
                    for constraint in inspector.get_check_constraints(table, schema=schema):
                        if constraint.get("dialect_options", {}).get("not_valid"):
                            invalid_constraints.append(f"{key}.{constraint['name']}")
                return {
                    "database": expected,
                    "server_version": sync_connection.exec_driver_sql(
                        "SHOW server_version"
                    ).scalar(),
                    "migration": sync_connection.exec_driver_sql(
                        "SELECT version_num FROM alembic_version"
                    ).scalar(),
                    "tables": len(database_tables),
                    "model_tables": len(model_tables),
                    "missing_tables": missing,
                    "extra_tables": extra,
                    "model_columns": model_column_count,
                    "database_columns": database_column_count,
                    "missing_columns": sorted(missing_columns),
                    "extra_columns": sorted(extra_columns),
                    "timezone_type_issues": sorted(timezone_issues),
                    "invalid_constraints": invalid_constraints,
                }

            return await connection.run_sync(inspect_schema)
    finally:
        await engine.dispose()


async def main():
    config = dotenv_values(".env")
    results = {}
    for label, key, database in (
        ("development", "DATABASE_URL", "quickbuddy_dev"),
        ("test", "TEST_DATABASE_URL", "quickbuddy_test"),
    ):
        url = os.environ.get(key) or config.get(key)
        if url and "REPLACE_ME" not in url:
            results[label] = await audit(url, database)
    destination = Path("docs/operations/phase-2a-schema-evidence.json")
    destination.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for label, evidence in results.items():
        print(
            label,
            {key: value for key, value in evidence.items() if key != "server_version"}
            | {"server_version": evidence["server_version"]},
        )
    print(destination)


if __name__ == "__main__":
    asyncio.run(main())
