"""Real quote/confirmation/accounting; geographic coverage is isolated in this test."""

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select

from backend.application import commerce
from backend.persistence.foundations import FOUNDATION_MODELS as F
from tests.integration.helpers import post, world


async def test_multi_restaurant_delivery_quote_and_repricing(api, monkeypatch):
    client, app = api
    state = await world(client, app, 2)

    async def covered(*args, **kwargs):
        return None

    monkeypatch.setattr(commerce, "serviceable", covered)
    for shop, fee in zip(state["shops"], ("25.00", "35.00"), strict=True):
        path = f"/api/v1/channel/branches/{shop['branch']['id']}/delivery-fee"
        denied = await client.put(
            path, json={"currency": "XTS", "amount": fee}, headers=state["customer"]["headers"]
        )
        assert denied.status_code == 403
        response = await client.put(
            path, json={"currency": "XTS", "amount": fee}, headers=shop["merchant"]["headers"]
        )
        assert response.status_code == 200, response.text
    wrong_merchant = await client.put(
        f"/api/v1/channel/branches/{state['shops'][0]['branch']['id']}/delivery-fee",
        json={"currency": "XTS", "amount": "0.00"},
        headers=state["shops"][1]["merchant"]["headers"],
    )
    assert wrong_merchant.status_code == 403
    address = await post(
        client,
        "/addresses",
        {
            "city_id": state["city"]["id"],
            "label": "Test",
            "address_text": "Integration address",
            "latitude": "0",
            "longitude": "0",
        },
        state["customer"],
    )

    async def quote():
        cart = await post(client, "/carts", {}, state["customer"])
        for shop in state["shops"]:
            await post(
                client,
                f"/carts/{cart['id']}/items",
                {
                    "branch_id": shop["branch"]["id"],
                    "variant_id": shop["variant"]["id"],
                    "quantity": "1",
                    "window_id": shop["window"]["id"],
                    "address_id": address["id"],
                    "delivery_method": "courier",
                },
                state["customer"],
            )
        return await post(client, f"/carts/{cart['id']}/quote", {}, state["customer"])

    review = await quote()
    assert Decimal(review["total"]) == Decimal("80.00")
    assert sorted(Decimal(g["delivery_fee"]) for g in review["shipments"]) == [
        Decimal("25"),
        Decimal("35"),
    ]
    assert len(review["shipments"]) == 2 and all(
        g["estimated_arrival_start"] for g in review["shipments"]
    )
    order = await post(
        client,
        "/orders/confirm",
        {"quote_id": review["id"]},
        state["customer"],
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert Decimal(order["total"]) == Decimal("80.00")
    children = await client.get(
        f"/api/v1/orders/{order['id']}/merchant-orders", headers=state["customer"]["headers"]
    )
    assert len(children.json()["items"]) == 2
    assert sum(Decimal(c["total"]) for c in children.json()["items"]) == Decimal("20.00")
    async with app.state.sessions() as db:
        model = F["commerce.order_amount_breakdowns"]
        amount = await db.scalar(
            select(model.amount).where(
                model.order_id == UUID(order["id"]), model.kind == "delivery"
            )
        )
        assert amount == Decimal("60.00")
    intent = await post(
        client, "/finance/sandbox/payment-intents", {"order_id": order["id"]}, state["customer"]
    )
    assert Decimal(intent["amount"]) == Decimal("80.00")
    stale = await quote()
    shop = state["shops"][0]
    response = await client.put(
        f"/api/v1/channel/branches/{shop['branch']['id']}/delivery-fee",
        json={"currency": "XTS", "amount": "30.00"},
        headers=shop["merchant"]["headers"],
    )
    assert response.status_code == 200
    rejected = await client.post(
        "/api/v1/orders/confirm",
        json={"quote_id": stale["id"]},
        headers={**state["customer"]["headers"], "Idempotency-Key": uuid4().hex},
    )
    assert rejected.status_code == 409 and rejected.json()["error"]["code"] == "price_changed"
