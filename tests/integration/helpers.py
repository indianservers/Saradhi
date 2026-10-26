from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select

from backend.application.common import add, now
from backend.persistence import models as m


async def user(client, app, role=None):
    email = f"integration-{uuid4().hex}@example.test"
    password = "Test-only!" + uuid4().hex
    registered = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert registered.status_code == 201, registered.text
    uid = registered.json()["id"]
    if role:
        async with app.state.sessions.begin() as db:
            assigned = await db.scalar(select(m.Role).where(m.Role.name == role))
            await add(db, m.RoleAssignment, user_id=uid, role_id=assigned.id)
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {
        "id": uid,
        "email": email,
        "password": password,
        "tokens": login.json(),
        "headers": {"Authorization": "Bearer " + login.json()["access_token"]},
    }


async def post(client, path, body, identity, expected=201, headers=None):
    response = await client.post(
        "/api/v1" + path, json=body, headers={**identity["headers"], **(headers or {})}
    )
    assert response.status_code == expected, response.text
    return response.json() if response.content else None


async def setup_shop(client, app, admin, merchant, city_id, category_id, index=0):
    organization = await post(
        client, "/organizations", {"name": f"Integration merchant {uuid4().hex}"}, merchant
    )
    brand = await post(
        client,
        "/merchants/brands",
        {
            "organization_id": organization["id"],
            "name": "Integration brand",
            "merchant_type": "food",
        },
        merchant,
    )
    branch = await post(
        client,
        "/merchants/branches",
        {
            "brand_id": brand["id"],
            "city_id": city_id,
            "name": "Integration branch",
            "latitude": "17.385",
            "longitude": "78.4867",
        },
        merchant,
    )
    await post(
        client,
        f"/merchants/branches/{branch['id']}/review",
        {
            "decision": "approved",
            "expected_version": 1,
            "reason": "Dedicated integration fixture review",
        },
        admin,
        200,
    )
    start = (now() + timedelta(days=2)).replace(hour=7 + index, minute=0, second=0, microsecond=0)
    # UTC city makes branch hours independent of machine timezone/DST.
    for weekday in range(7):
        await post(
            client,
            f"/merchants/branches/{branch['id']}/hours",
            {"weekday": weekday, "opens_at": "00:00:00", "closes_at": "23:59:59"},
            merchant,
        )
    await post(
        client, f"/merchants/branches/{branch['id']}/capabilities", {"method": "pickup"}, merchant
    )
    window = await post(
        client,
        f"/merchants/branches/{branch['id']}/windows",
        {
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=1)).isoformat(),
            "capacity": 100,
        },
        merchant,
    )
    product = await post(
        client,
        "/catalog/products",
        {
            "organization_id": organization["id"],
            "category_id": category_id,
            "name": "Integration product",
        },
        merchant,
    )
    variant = await post(
        client,
        f"/catalog/products/{product['id']}/variants",
        {"name": "Standard", "sku": uuid4().hex},
        merchant,
    )
    await post(
        client,
        f"/merchants/branches/{branch['id']}/prices",
        {
            "variant_id": variant["id"],
            "amount": "10.00",
            "currency": "XTS",
            "starts_at": now().isoformat(),
        },
        merchant,
    )
    stock = await post(
        client,
        f"/inventory/branches/{branch['id']}/adjustments",
        {"variant_id": variant["id"], "delta": "10", "idempotency_key": uuid4().hex},
        merchant,
        200,
    )
    return {
        "organization": organization,
        "branch": branch,
        "window": window,
        "product": product,
        "variant": variant,
        "stock": stock,
        "merchant": merchant,
    }


async def world(client, app, count=2):
    admin = await user(client, app, "platform_super_admin")
    customer = await user(client, app)
    # XTS is an explicitly test-only ISO code. Do not seed fixture business records in dev.
    async with app.state.sessions.begin() as db:
        currency = await db.scalar(select(m.Currency).where(m.Currency.code == "XTS"))
        if currency is None:
            await add(db, m.Currency, code="XTS", scale=2)
        country = await db.scalar(select(m.Country).where(m.Country.code == "ZZ"))
        if country is None:
            country = await add(db, m.Country, code="ZZ", name="Integration test country")
        country_id = str(country.id)
    city = await post(
        client,
        "/geo/cities",
        {"country_id": country_id, "name": uuid4().hex, "timezone": "UTC"},
        admin,
    )
    category = await post(
        client, "/catalog/categories", {"name": "Integration " + uuid4().hex}, admin
    )
    zone = await post(
        client, "/geo/zones", {"city_id": city["id"], "name": "Integration zone"}, admin
    )
    category_enabled = await client.put(
        f"/api/v1/geo/zones/{zone['id']}/categories",
        json={"category_id": category["id"], "enabled": True},
        headers=admin["headers"],
    )
    assert category_enabled.status_code == 200, category_enabled.text
    shops = []
    for index in range(count):
        merchant = await user(client, app)
        shops.append(
            await setup_shop(client, app, admin, merchant, city["id"], category["id"], index)
        )
    if shops:
        activation = await client.post(
            f"/api/v1/operations/cities/{city['id']}/activate",
            headers=admin["headers"],
        )
        assert activation.status_code == 200, activation.text
        city["active"] = True
    return {
        "admin": admin,
        "customer": customer,
        "city": city,
        "category": category,
        "zone": zone,
        "country_id": country_id,
        "shops": shops,
    }


async def checkout(client, customer, shops, key=None):
    cart = await post(client, "/carts", None, customer)
    for shop in shops:
        await post(
            client,
            f"/carts/{cart['id']}/items",
            {
                "branch_id": shop["branch"]["id"],
                "variant_id": shop["variant"]["id"],
                "quantity": "1",
                "window_id": shop["window"]["id"],
            },
            customer,
        )
    quote = await post(client, f"/carts/{cart['id']}/quote", None, customer)
    key = key or uuid4().hex
    order = await post(
        client,
        "/orders/confirm",
        {"quote_id": quote["id"]},
        customer,
        headers={"Idempotency-Key": key},
    )
    return cart, quote, order, key
