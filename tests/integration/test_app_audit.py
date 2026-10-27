"""Request-boundary regressions plus role-to-role order and tracking checks."""

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from backend.application.common import add, now
from backend.persistence import models as m
from tests.integration.helpers import checkout, post, user, world

INVALID_IDS = ["", "bad-id", "123", "null", "../orders", "' OR 1=1", [], {}, 123, True, None, "😀"]
INVALID_QUANTITIES = [
    "0",
    "-1",
    "-0.0001",
    "1.00001",
    "NaN",
    "Infinity",
    {},
    [],
    None,
    "",
    "1e99",
    True,
]
CART_CASES = (
    [(field, value) for field in ["branch_id", "variant_id", "window_id"] for value in INVALID_IDS]
    + [("quantity", value) for value in INVALID_QUANTITIES]
    + [
        ("delivery_method", value)
        for value in [
            "",
            "drone",
            "PICKUP",
            "delivery",
            "../pickup",
            "courier;",
            [],
            {},
            1,
            True,
            None,
            "😀",
        ]
    ]
)


@pytest.mark.parametrize(
    "field,value", CART_CASES, ids=[f"cart-{field}-{i}" for i, (field, _) in enumerate(CART_CASES)]
)
async def test_cart_rejects_invalid_line_without_mutation(api, field, value):
    client, app = api
    customer = await user(client, app)
    cart = await post(client, "/carts", None, customer)
    body = {
        "branch_id": str(uuid4()),
        "variant_id": str(uuid4()),
        "window_id": str(uuid4()),
        "quantity": "1",
        "delivery_method": "pickup",
    }
    response = await client.post(
        f"/api/v1/carts/{cart['id']}/items",
        json={**body, field: value},
        headers=customer["headers"],
    )
    assert response.status_code == 422, response.text
    current = await client.get(f"/api/v1/carts/{cart['id']}/items", headers=customer["headers"])
    assert current.status_code == 200 and current.json()["items"] == []


@pytest.mark.parametrize(
    "path",
    [
        "/orders",
        "/addresses",
        "/catalog/products",
        "/catalog/categories",
        "/geo/countries",
        "/geo/cities",
        "/merchant/branches",
    ],
)
@pytest.mark.parametrize("limit", ["0", "-1", "101", "1.5", "NaN"])
async def test_app_lists_reject_unbounded_or_invalid_page_sizes(api, path, limit):
    client, app = api
    customer = await user(client, app)
    response = await client.get(
        f"/api/v1{path}", params={"limit": limit}, headers=customer["headers"]
    )
    assert response.status_code == 422, response.text


async def test_restaurant_details_are_branch_scoped_and_customer_changes_are_visible(api):
    client, app = api
    state = await world(client, app, 2)
    shop, other = state["shops"]
    _, _, order, _ = await checkout(client, state["customer"], [shop])
    children = (
        await client.get(
            f"/api/v1/orders/{order['id']}/merchant-orders", headers=state["customer"]["headers"]
        )
    ).json()["items"]
    child = children[0]
    path = f"/merchant/branches/{shop['branch']['id']}/orders/{child['id']}"
    detail = await client.get("/api/v1" + path, headers=shop["merchant"]["headers"])
    assert detail.status_code == 200, detail.text
    assert detail.json()["customer"] == {"display_name": "Customer"}
    assert detail.json()["items"][0]["product_name"] == "Integration product"
    assert "email" not in detail.json()["customer"]
    assert detail.json()["fulfillment"][0]["address"] is None
    for identity in [state["customer"], other["merchant"]]:
        assert (await client.get("/api/v1" + path, headers=identity["headers"])).status_code == 403
    mismatch = path.replace(shop["branch"]["id"], other["branch"]["id"])
    assert (
        await client.get("/api/v1" + mismatch, headers=other["merchant"]["headers"])
    ).status_code == 404
    await post(
        client,
        f"/merchant-orders/{child['id']}/transition",
        {"target": "accepted", "expected_version": child["version"]},
        shop["merchant"],
        200,
    )
    changed = await client.get(
        f"/api/v1/orders/{order['id']}/merchant-orders", headers=state["customer"]["headers"]
    )
    assert changed.json()["items"][0]["status"] == "accepted"


async def test_tracking_immediately_hides_revoked_stale_and_terminal_locations(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    identity = await user(client, app)
    async with app.state.sessions.begin() as db:
        pilot = await add(
            db,
            m.Pilot,
            user_id=UUID(identity["id"]),
            city_id=UUID(state["city"]["id"]),
            verified=True,
            state="assigned",
            location_consent_at=now(),
            location_consent_version="pilot-location-v1",
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
            pilot_id=pilot.id,
            status="accepted",
            expires_at=now() + timedelta(minutes=5),
        )
        await add(
            db,
            m.LatestLocation,
            pilot_id=pilot.id,
            latitude="17.385",
            longitude="78.4867",
            accuracy_m="5",
            observed_at=now(),
            client_sequence=1,
            app_state="foreground",
        )
        pilot_id, task_id = pilot.id, task.id
    path = f"/api/v1/orders/{order['id']}/tracking"

    async def location():
        response = await client.get(path, headers=state["customer"]["headers"])
        assert response.status_code == 200, response.text
        return response.json()["deliveries"][0]["pilot_location"]

    assert (await location())["latitude"] == "17.3850000"
    assert (await client.get(path, headers=identity["headers"])).status_code == 403
    async with app.state.sessions.begin() as db:
        pilot = await db.get(m.Pilot, pilot_id)
        pilot.location_consent_at = pilot.location_consent_version = None
    assert await location() is None
    async with app.state.sessions.begin() as db:
        pilot = await db.get(m.Pilot, pilot_id)
        pilot.location_consent_at, pilot.location_consent_version = now(), "pilot-location-v1"
        latest = await db.scalar(
            select(m.LatestLocation).where(m.LatestLocation.pilot_id == pilot_id)
        )
        latest.observed_at = now() - timedelta(minutes=10)
    assert await location() is None
    async with app.state.sessions.begin() as db:
        latest = await db.scalar(
            select(m.LatestLocation).where(m.LatestLocation.pilot_id == pilot_id)
        )
        latest.observed_at = now()
        (await db.get(m.DeliveryTask, task_id)).status = "delivered"
    assert await location() is None


async def test_new_menu_variant_can_be_stocked_before_customer_purchase(api):
    client, app = api
    state = await world(client, app, 1)
    shop = state["shops"][0]
    merchant = shop["merchant"]
    variant = await post(
        client,
        f"/catalog/products/{shop['product']['id']}/variants",
        {"name": "New size", "sku": uuid4().hex},
        merchant,
    )
    await post(
        client,
        f"/merchants/branches/{shop['branch']['id']}/prices",
        {
            "variant_id": variant["id"],
            "currency": "XTS",
            "amount": "7.50",
            "starts_at": now().isoformat(),
        },
        merchant,
    )
    inventory = await client.get(
        f"/api/v1/inventory/branches/{shop['branch']['id']}", headers=merchant["headers"]
    )
    balance = next(row for row in inventory.json()["items"] if row["variant_id"] == variant["id"])
    assert float(balance["on_hand"]) == 0
    path = f"/api/v1/catalog/products?branch_id={shop['branch']['id']}"
    assert not any(
        row["variant_id"] == variant["id"]
        for row in (await client.get(path, headers=state["customer"]["headers"])).json()["items"]
    )
    await post(
        client,
        f"/inventory/branches/{shop['branch']['id']}/adjustments",
        {"variant_id": variant["id"], "delta": "5", "idempotency_key": uuid4().hex},
        merchant,
        200,
    )
    catalog = (await client.get(path, headers=state["customer"]["headers"])).json()["items"]
    product = next(row for row in catalog if row["variant_id"] == variant["id"])
    assert float(product["available_quantity"]) == 5
    assert float(product["unit_price"]) == 7.5
