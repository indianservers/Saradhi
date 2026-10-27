"""Create a synthetic two-device voice fixture in local quickbuddy_test only."""

import asyncio
import json
from datetime import timedelta
from pathlib import Path
from uuid import UUID

from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url

from backend.api.app.main import create_app
from backend.application.common import add, now
from backend.persistence import models as m
from backend.shared.settings import Settings
from tests.integration.helpers import checkout, user, world

ROOT = Path(__file__).resolve().parents[1]


async def main():
    url = dotenv_values(ROOT / ".env")["TEST_DATABASE_URL"]
    parsed = make_url(url)
    if parsed.database != "quickbuddy_test" or parsed.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("Voice QA only accepts local quickbuddy_test")
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=url,
        auth_private_key_path=str(ROOT / ".secrets/integration-test-private.pem"),
        auth_rate_limit_per_minute=10000,
        api_requests_per_minute=100000,
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://qa") as client:
            state = await world(client, app, 1)
            _, _, order, _ = await checkout(client, state["customer"], state["shops"])
            pilot = await user(client, app)
            async with app.state.sessions.begin() as db:
                profile = await add(
                    db,
                    m.Pilot,
                    user_id=UUID(pilot["id"]),
                    city_id=UUID(state["city"]["id"]),
                    verified=True,
                    state="assigned",
                )
                unit = await db.scalar(
                    select(m.FulfillmentUnit)
                    .join(m.MerchantOrder)
                    .where(m.MerchantOrder.order_id == UUID(order["id"]))
                )
                task = await db.scalar(
                    select(m.DeliveryTask).where(m.DeliveryTask.fulfillment_unit_id == unit.id)
                )
                task.status = "assigned"
                await add(
                    db,
                    m.Assignment,
                    task_id=task.id,
                    pilot_id=profile.id,
                    status="accepted",
                    expires_at=now() + timedelta(hours=1),
                )
                task_id = str(task.id)
            for role, identity in [("customer", state["customer"]), ("pilot", pilot)]:
                values = {
                    "API_BASE_URL": "http://127.0.0.1:8002",
                    "QA_EMAIL": identity["email"],
                    "QA_PASSWORD": identity["password"],
                    "QA_DELIVERY_ID": task_id,
                    "QA_ORDER_ID": order["id"],
                }
                (ROOT / f".secrets/device-call-{role}.json").write_text(
                    json.dumps(values), encoding="utf-8"
                )
    print("Synthetic voice fixture created; device defines saved under ignored .secrets.")


if __name__ == "__main__":
    asyncio.run(main())
