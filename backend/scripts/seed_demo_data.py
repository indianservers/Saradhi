"""Create a reusable synthetic Quickbuddy demo world in the isolated local dev DB.

The script refuses every database except quickbuddy_dev on the project's local 5433
PostgreSQL cluster. It creates no production/provider transactions. Credentials are
randomly generated and saved only under ignored .secrets/.
"""

import asyncio
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url

from backend.api.app.main import create_app
from backend.application.common import add
from backend.persistence import models as m
from backend.shared.database import create_database
from backend.shared.settings import get_settings


ROOT = Path(__file__).resolve().parents[2]
SECRET_FILE = ROOT / ".secrets" / "quickbuddy-demo-accounts.json"
MARKER = "Quickbuddy Demo — Northstar Kitchen"


def guarded_settings():
    settings = get_settings()
    url = make_url(settings.database_url.get_secret_value())
    if not (
        settings.app_env == "development"
        and url.drivername == "postgresql+asyncpg"
        and url.database == "quickbuddy_dev"
        and url.host in {"127.0.0.1", "localhost", "::1"}
        and url.port == 5433
    ):
        raise SystemExit(
            "Refusing to seed: this command is restricted to development quickbuddy_dev "
            "on localhost:5433."
        )
    return settings


def load_accounts():
    if SECRET_FILE.exists():
        accounts = json.loads(SECRET_FILE.read_text(encoding="utf-8"))
    else:
        accounts = {}
        for key, email in {
            "admin": "demo.admin@example.test",
            "customer": "demo.customer@example.test",
            "customer_two": "demo.customer2@example.test",
            "restaurant": "demo.restaurant@example.test",
            "market": "demo.market@example.test",
            "pilot": "demo.pilot@example.test",
            "support": "demo.support@example.test",
        }.items():
            accounts[key] = {"email": email, "password": secrets.token_urlsafe(24)}
        SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
        SECRET_FILE.write_text(json.dumps(accounts, indent=2) + "\n", encoding="utf-8")
        try:
            SECRET_FILE.chmod(0o600)
        except OSError:
            pass
    expected = {"admin", "customer", "customer_two", "restaurant", "market", "pilot", "support"}
    if set(accounts) != expected:
        raise SystemExit(f"Unexpected demo account file format: {SECRET_FILE}")
    return accounts


async def main():
    settings = guarded_settings()
    accounts = load_accounts()
    # Fast no-op on rerun; never duplicate or rewrite any seeded business rows.
    engine = create_database(settings)
    async with engine.connect() as connection:
        marker_id = await connection.scalar(
            select(m.Organization.id).where(m.Organization.name == MARKER).limit(1)
        )
        if marker_id:
            checks = {
                "demo users": await connection.scalar(
                    select(m.Email.id).where(m.Email.address == "demo.support@example.test").limit(1)
                ),
                "both merchants": await connection.scalar(
                    select(m.Organization.id)
                    .where(m.Organization.name == "Sunrise Market")
                    .limit(1)
                ),
                "demo order": await connection.scalar(
                    select(m.Order.id)
                    .join(m.Email, m.Email.user_id == m.Order.user_id)
                    .where(m.Email.address == "demo.customer@example.test")
                    .limit(1)
                ),
                "demo pilot": await connection.scalar(
                    select(m.Pilot.id)
                    .join(m.User, m.User.id == m.Pilot.user_id)
                    .join(m.Email, m.Email.user_id == m.User.id)
                    .where(m.Email.address == "demo.pilot@example.test")
                    .limit(1)
                ),
                "demo support case": await connection.scalar(
                    select(m.Ticket.id)
                    .join(m.Email, m.Email.user_id == m.Ticket.user_id)
                    .where(m.Email.address == "demo.customer@example.test")
                    .limit(1)
                ),
            }
        else:
            checks = {}
    await engine.dispose()
    if marker_id and all(checks.values()):
        print("Quickbuddy demo data is already present in quickbuddy_dev; no rows changed.")
        print(f"Demo account credentials: {SECRET_FILE}")
        return
    if marker_id:
        missing = ", ".join(name for name, value in checks.items() if not value)
        raise SystemExit(
            "A partial Quickbuddy demo seed was found. No rows changed. "
            f"Inspect quickbuddy_dev before continuing; missing: {missing}."
        )

    app = create_app(settings)
    counts = {"users": 0, "restaurants_or_stores": 0}
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://demo.local"
        ) as client:
            identities = {}
            for key, item in accounts.items():
                response = await client.post(
                    "/api/v1/auth/register",
                    json={"email": item["email"], "password": item["password"]},
                )
                if response.status_code not in (201, 409):
                    raise RuntimeError(f"Demo registration failed ({response.status_code}): {response.text}")
                login = await client.post(
                    "/api/v1/auth/login",
                    json={"email": item["email"], "password": item["password"]},
                )
                if login.status_code != 200:
                    raise RuntimeError(f"Demo sign-in failed for {item['email']}: {login.text}")
                identities[key] = {
                    "id": response.json()["id"] if response.status_code == 201 else None,
                    "email": item["email"],
                    "headers": {"Authorization": "Bearer " + login.json()["access_token"]},
                }
                if response.status_code == 201:
                    counts["users"] += 1

            # Grant only the explicitly named local demo operators their demo scopes.
            async with app.state.sessions.begin() as db:
                for key, role_name in (
                    ("admin", "platform_super_admin"),
                    ("pilot", "delivery_pilot"),
                    ("support", "support_agent"),
                ):
                    user_id = await db.scalar(
                        select(m.Email.user_id).where(m.Email.address == accounts[key]["email"])
                    )
                    role = await db.scalar(select(m.Role).where(m.Role.name == role_name))
                    if not user_id or not role:
                        raise RuntimeError(f"Required demo identity role is missing: {role_name}")
                    prior = await db.scalar(
                        select(m.RoleAssignment.id).where(
                            m.RoleAssignment.user_id == user_id,
                            m.RoleAssignment.role_id == role.id,
                            m.RoleAssignment.organization_id.is_(None),
                            m.RoleAssignment.city_id.is_(None),
                            m.RoleAssignment.branch_id.is_(None),
                        )
                    )
                    if not prior:
                        await add(db, m.RoleAssignment, user_id=user_id, role_id=role.id)
                if not await db.scalar(select(m.Currency.code).where(m.Currency.code == "INR")):
                    await add(db, m.Currency, code="INR", scale=2)

            async def call(method, path, identity, body=None, expected=(200, 201, 204), headers=None):
                response = await client.request(
                    method,
                    "/api/v1" + path,
                    json=body,
                    headers={**identity["headers"], **(headers or {})},
                )
                if response.status_code not in expected:
                    raise RuntimeError(
                        f"Demo seed {method} {path} returned {response.status_code}: {response.text}"
                    )
                return response.json() if response.content else None

            admin = identities["admin"]
            country = await call("POST", "/geo/countries", admin, {"code": "IN", "name": "India"})
            city = await call(
                "POST", "/geo/cities", admin,
                {"country_id": country["id"], "name": "Demo City", "timezone": "Asia/Kolkata"},
            )
            category_ids = {}
            for name in ("Demo Food", "Demo Grocery"):
                category_ids[name] = await call(
                    "POST", "/catalog/categories", admin, {"name": name, "regulated": False}
                )
            zone = await call("POST", "/geo/zones", admin, {"city_id": city["id"], "name": "Central Demo Zone"})
            for category in category_ids.values():
                await call(
                    "PUT", f"/geo/zones/{zone['id']}/categories", admin,
                    {"category_id": category["id"], "enabled": True},
                )

            shops = []
            shop_data = (
                ("restaurant", "Northstar Kitchen", "Northstar Kitchen", "food", "Demo Food", "Masala Dosa", "Classic", "189.00"),
                ("market", "Sunrise Market", "Sunrise Market", "grocery", "Demo Grocery", "Alphonso Mangoes", "1 kg", "249.00"),
            )
            for index, (account_key, org_name, brand_name, kind, category_name, product_name, variant_name, price) in enumerate(shop_data):
                owner = identities[account_key]
                org = await call("POST", "/organizations", owner, {"name": MARKER if index == 0 else org_name})
                brand = await call(
                    "POST", "/merchants/brands", owner,
                    {"organization_id": org["id"], "name": brand_name, "merchant_type": kind},
                )
                branch = await call(
                    "POST", "/merchants/branches", owner,
                    {"brand_id": brand["id"], "city_id": city["id"], "name": brand_name + " — Demo City", "latitude": "18.5204", "longitude": "73.8567"},
                )
                branch = await call(
                    "POST", f"/merchants/branches/{branch['id']}/review", admin,
                    {"decision": "approved", "expected_version": branch["version"], "reason": "Synthetic local demo merchant"},
                )
                for weekday in range(7):
                    await call(
                        "POST", f"/merchants/branches/{branch['id']}/hours", owner,
                        {"weekday": weekday, "opens_at": "08:00:00", "closes_at": "22:00:00"},
                    )
                await call("POST", f"/merchants/branches/{branch['id']}/capabilities", owner, {"method": "pickup"})
                start = (datetime.now(timezone.utc) + timedelta(days=2)).replace(hour=5, minute=0, second=0, microsecond=0)
                window = await call(
                    "POST", f"/merchants/branches/{branch['id']}/windows", owner,
                    {"starts_at": start.isoformat(), "ends_at": (start + timedelta(hours=2)).isoformat(), "capacity": 100},
                )
                product = await call(
                    "POST", "/catalog/products", owner,
                    {"organization_id": org["id"], "category_id": category_ids[category_name]["id"], "name": product_name, "unit": "each"},
                )
                variant = await call(
                    "POST", f"/catalog/products/{product['id']}/variants", owner,
                    {"name": variant_name, "sku": f"QB-DEMO-{index + 1:02d}"},
                )
                await call(
                    "POST", f"/merchants/branches/{branch['id']}/prices", owner,
                    {"variant_id": variant["id"], "currency": "INR", "amount": price, "starts_at": datetime.now(timezone.utc).isoformat()},
                )
                await call(
                    "POST", f"/inventory/branches/{branch['id']}/adjustments", owner,
                    {"variant_id": variant["id"], "delta": "50", "idempotency_key": f"quickbuddy-demo-stock-{index + 1:02d}"},
                )
                shops.append({"organization": org, "branch": branch, "product": product, "variant": variant, "window": window, "owner": owner})
                counts["restaurants_or_stores"] += 1

            await call("POST", f"/operations/cities/{city['id']}/activate", admin)

            customer = identities["customer"]
            address = await call(
                "POST", "/addresses", customer,
                {"city_id": city["id"], "label": "Home", "address_text": "Demo Apartment, Central Demo City", "latitude": "18.5204", "longitude": "73.8567"},
            )
            cart = await call("POST", "/carts", customer, None)
            first = shops[0]
            await call(
                "POST", f"/carts/{cart['id']}/items", customer,
                {"branch_id": first["branch"]["id"], "variant_id": first["variant"]["id"], "quantity": "1", "window_id": first["window"]["id"], "delivery_method": "pickup", "preparation_notes": "Demo order"},
            )
            quote = await call("POST", f"/carts/{cart['id']}/quote", customer, None)
            await call(
                "POST", "/orders/confirm", customer, {"quote_id": quote["id"]},
                expected=(201,), headers={"Idempotency-Key": "quickbuddy-demo-order-0001"},
            )
            await call("POST", "/support/tickets", customer, {"subject": "Demo order status question"})

            pilot = identities["pilot"]
            pilot_profile = await call("POST", "/pilots", pilot, {"city_id": city["id"]})
            await call("POST", f"/pilots/{pilot_profile['id']}/verify", admin)

            # Verify visible customer catalog and order workflows, without any payment provider call.
            catalog = await call("GET", f"/catalog/products?city_id={city['id']}", customer)
            orders = await call("GET", "/orders", customer)
            if len(catalog["items"]) < 2 or not orders["items"]:
                raise RuntimeError("Demo data was created but catalog/order verification failed")

    print("Quickbuddy demo data seeded into the isolated quickbuddy_dev database.")
    print("Includes admin, customer, restaurant, grocery, pilot and support accounts; two merchants, catalogue, inventory, order and support ticket.")
    print(f"Demo account credentials: {SECRET_FILE}")
    print("No production services, payment provider, or third-party APIs were called.")


if __name__ == "__main__":
    asyncio.run(main())
