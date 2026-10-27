from decimal import Decimal
from uuid import UUID, uuid4

from backend.application.common import add
from backend.persistence.foundations import FOUNDATION_MODELS as F
from tests.integration.helpers import post, world


async def test_live_metadata_option_pricing_and_merchant_scope(api):
    client, app = api
    state = await world(client, app, 1)
    shop = state["shops"][0]
    path = f"/api/v1/channel/products/{shop['product']['id']}/details"
    body = {
        "ingredients": ["rice", "milk"],
        "dietary": ["vegetarian"],
        "allergens": ["milk"],
        "allergens_reviewed": True,
        "groups": [
            {
                "name": "Extras",
                "minimum": 1,
                "maximum": 1,
                "values": [{"name": "Extra portion", "price_delta": "0.50"}],
            }
        ],
    }
    forbidden = await client.put(path, json=body, headers=state["customer"]["headers"])
    assert forbidden.status_code == 403
    response = await client.put(path, json=body, headers=shop["merchant"]["headers"])
    assert response.status_code == 200, response.text
    catalog = await client.get(
        f"/api/v1/channel/catalog?branch_id={shop['branch']['id']}",
        headers=state["customer"]["headers"],
    )
    assert catalog.status_code == 200, catalog.text
    row = catalog.json()["items"][0]
    assert row["ingredients"] == ["rice", "milk"]
    assert row["allergens_reviewed"] and row["dietary"] == ["vegetarian"]
    option = row["groups"][0]["values"][0]["id"]
    cart = await post(client, "/carts", {}, state["customer"])
    await post(
        client,
        f"/carts/{cart['id']}/items",
        {
            "branch_id": shop["branch"]["id"],
            "variant_id": shop["variant"]["id"],
            "quantity": "2",
            "window_id": shop["window"]["id"],
            "delivery_method": "pickup",
            "option_ids": [option],
            "preparation_notes": "Mild please",
        },
        state["customer"],
    )
    quote = await post(client, f"/carts/{cart['id']}/quote", {}, state["customer"])
    assert Decimal(quote["total"]) == Decimal("21.00")
    assert quote["lines"][0]["addons"][0]["name"] == "Extra portion"
    assert quote["lines"][0]["preparation_notes"] == "Mild please"
    order = await post(
        client,
        "/orders/confirm",
        {"quote_id": quote["id"]},
        state["customer"],
        headers={"Idempotency-Key": uuid4().hex},
    )
    children = await client.get(
        f"/api/v1/orders/{order['id']}/merchant-orders", headers=state["customer"]["headers"]
    )
    assert all(row["status"] == "pending" for row in children.json()["items"])
    async with app.state.sessions.begin() as db:
        await add(
            db,
            F["catalog.product_branch_availability"],
            branch_id=UUID(shop["branch"]["id"]),
            variant_id=UUID(shop["variant"]["id"]),
            available=False,
        )
    unavailable = await client.get(
        f"/api/v1/channel/catalog?branch_id={shop['branch']['id']}",
        headers=state["customer"]["headers"],
    )
    assert unavailable.json()["items"] == []
