"""Create isolated, synthetic app audit identities in loopback quickbuddy_test."""

import asyncio
import json
from pathlib import Path

from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url

from backend.api.app.main import create_app
from backend.shared.settings import Settings
from tests.integration.helpers import checkout, post, user, world


async def main():
    root = Path(__file__).resolve().parents[1]
    url = dotenv_values(root / ".env")["TEST_DATABASE_URL"]
    parsed = make_url(url)
    if parsed.database != "quickbuddy_test" or parsed.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("App QA refuses any database except local quickbuddy_test")
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=url,
        auth_private_key_path=str(root / ".secrets/integration-test-private.pem"),
        auth_rate_limit_per_minute=10000,
        api_requests_per_minute=100000,
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app, client=("127.99.0.1", 123)), base_url="http://qa"
        ) as client:
            state = await world(client, app, 2)
            _, _, order, _ = await checkout(client, state["customer"], [state["shops"][0]])
            pilot = await user(client, app)
            profile = await post(client, "/pilots", {"city_id": state["city"]["id"]}, pilot)
            await post(client, f"/pilots/{profile['id']}/verify", None, state["admin"], 200)
            children = (
                await client.get(
                    f"/api/v1/orders/{order['id']}/merchant-orders",
                    headers=state["customer"]["headers"],
                )
            ).json()["items"]
            for role, identity in [
                ("customer", state["customer"]),
                ("pilot", pilot),
                ("merchant", state["shops"][0]["merchant"]),
                ("company", state["admin"]),
            ]:
                values = {
                    "API_BASE_URL": "http://127.0.0.1:8001",
                    "QA_EMAIL": identity["email"],
                    "QA_PASSWORD": identity["password"],
                    "QA_ORDER_ID": order["id"],
                    "QA_CHILD_ID": children[0]["id"],
                    "QA_BRANCH_ID": state["shops"][0]["branch"]["id"],
                    "QA_CITY_ID": state["city"]["id"],
                    "QA_CUSTOMER_EMAIL": state["customer"]["email"],
                    "QA_CUSTOMER_PASSWORD": state["customer"]["password"],
                }
                (root / f".secrets/device-audit-{role}.json").write_text(
                    json.dumps(values), encoding="utf-8"
                )
    print("Synthetic app audit fixtures saved privately under .secrets.")


if __name__ == "__main__":
    asyncio.run(main())
