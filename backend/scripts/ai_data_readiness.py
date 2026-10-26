"""Count AI training labels without selecting customer or pilot PII."""

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.engine import make_url

from backend.shared.database import create_database
from backend.shared.settings import Settings


async def inspect(database_url, expected):
    url = make_url(database_url)
    if url.database != expected or url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit(f"Refusing AI data audit outside local {expected}")
    engine = create_database(Settings(_env_file=None, app_env="test", database_url=database_url))
    statements = {
        "orders_total": "SELECT count(*) FROM commerce.orders",
        "orders_last_28d": (
            "SELECT count(*) FROM commerce.orders WHERE created_at >= now()-interval '28 days'"
        ),
        "merchant_orders_total": "SELECT count(*) FROM commerce.merchant_orders",
        "merchant_orders_ready_or_fulfilled": (
            "SELECT count(*) FROM commerce.merchant_orders WHERE status IN ('ready','fulfilled')"
        ),
        "completed_delivery_tasks": (
            "SELECT count(*) FROM fulfillment.delivery_tasks WHERE status='delivered'"
        ),
        "delivery_confirmations": "SELECT count(*) FROM fulfillment.delivery_confirmations",
        "eta_estimates": "SELECT count(*) FROM fulfillment.eta_estimates",
        "cancellation_records": "SELECT count(*) FROM commerce.order_cancellations",
        "hourly_demand_buckets_last_28d": """SELECT count(*) FROM (
            SELECT date_trunc('hour', created_at) FROM commerce.orders
            WHERE created_at >= now()-interval '28 days' GROUP BY 1) buckets""",
    }
    try:
        async with engine.connect() as connection:
            counts = {
                key: int(await connection.scalar(text(statement)))
                for key, statement in statements.items()
            }
            counts["preparation_duration_labels"] = 0
            counts["note"] = (
                "No per-merchant-order preparation start/ready timestamp pair exists "
                "in current event schema."
            )
            counts["model_training_status"] = "untrained"
            counts["test_data_excluded"] = expected == "quickbuddy_test"
            return {
                "database": expected,
                "migration": await connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                ),
                "counts": counts,
            }
    finally:
        await engine.dispose()


async def main():
    config = dotenv_values(".env")
    results = {}
    for label, key, expected in (
        ("development", "DATABASE_URL", "quickbuddy_dev"),
        ("test", "TEST_DATABASE_URL", "quickbuddy_test"),
    ):
        value = os.environ.get(key) or config.get(key)
        if value and "REPLACE_ME" not in value:
            results[label] = await inspect(value, expected)
    results["generated_at"] = datetime.now(UTC).isoformat()
    target = Path("docs/ai/data-readiness.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
