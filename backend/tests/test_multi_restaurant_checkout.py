from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace as N
from uuid import uuid4

import pytest

from backend.application.checkout_groups import group_deliveries
from backend.domain.rules import BusinessError
from backend.integrations.telegram.bot import Store
from backend.tests.test_telegram_bot import message


def fixture_groups():
    branches, windows, rates, lines = {}, {}, {}, []
    for index in range(2):
        bid, wid = uuid4(), uuid4()
        branches[bid] = N(id=bid, name=f"Restaurant {index + 1}")
        windows[wid] = N(
            starts_at=datetime(2099, 1, 1, 10 + index, tzinfo=UTC),
            ends_at=datetime(2099, 1, 1, 11 + index, tzinfo=UTC),
        )
        rates[str(bid)] = {"amount": Decimal(25 + index * 10), "rule_id": str(uuid4())}
        for _ in range(2):
            lines.append(
                {
                    "cart_item_id": str(uuid4()),
                    "branch_id": str(bid),
                    "window_id": str(wid),
                    "delivery_method": "courier",
                    "address": {"id": "same-address"},
                    "total": "110.00",
                    "unit_price": "100.00",
                    "quantity": "1",
                }
            )
    return lines, branches, windows, rates


def test_fee_once_per_restaurant_and_separate_arrivals():
    lines, branches, windows, rates = fixture_groups()
    groups = group_deliveries(lines, branches, windows, rates, 2)
    assert len(groups) == 2
    assert [g["delivery_fee"] for g in groups] == ["25.00", "35.00"]
    assert [g["total"] for g in groups] == ["245.00", "255.00"]
    assert sum(Decimal(g["total"]) for g in groups) == Decimal("500.00")
    assert all(len(g["line_ids"]) == 2 and g["extras"] == "20.00" for g in groups)
    assert groups[0]["estimated_arrival_start"] != groups[1]["estimated_arrival_start"]
    assert all(g["estimate_basis"] == "merchant_scheduled_window" for g in groups)


def test_pickup_is_free_and_missing_delivery_rate_blocks_checkout():
    lines, branches, windows, rates = fixture_groups()
    with pytest.raises(BusinessError, match="pricing is not configured"):
        group_deliveries(lines, branches, windows, {}, 2)
    for line in lines:
        line["delivery_method"] = "pickup"
    groups = group_deliveries(lines, branches, windows, {}, 2)
    assert all(g["delivery_fee"] == "0.00" for g in groups)


def test_demo_combined_checkout_separate_fees_and_extras(tmp_path):
    store = Store(tmp_path / "multi.sqlite3")
    profile = {
        "location": {"latitude": 17.3, "longitude": 78.4},
        "basket": [
            {
                "selection": "demo_deccan/chicken",
                "item": "Chicken biryani",
                "restaurant": "Demo Deccan Kitchen",
                "quantity": 2,
                "price_minor": 24900,
                "options": [{"price_delta": "10.00"}],
            },
            {
                "selection": "demo_spice/veg",
                "item": "Veg biryani",
                "restaurant": "Demo Spice Table",
                "quantity": 1,
                "price_minor": 16900,
                "options": [],
            },
        ],
    }
    with store.db:
        store.save_profile(42, profile)
    response = store.process(message(1, "Delivery"))
    assert "Demo Deccan Kitchen" in response["text"] and "Demo Spice Table" in response["text"]
    assert (
        "Delivery fee: INR 25.00" in response["text"]
        and "Delivery fee: INR 35.00" in response["text"]
    )
    assert "Combined total: INR 747.00" in response["text"]
    assert "25-40 min" in response["text"] and "35-50 min" in response["text"]
    assert store.db.execute("SELECT count(*) FROM requests").fetchone()[0] == 0


@pytest.mark.asyncio
async def test_delivery_rate_override_latest_and_ambiguous_rules():
    from backend.application.checkout_groups import delivery_rates

    city, currency_id, bid = uuid4(), uuid4(), uuid4()
    branch = N(id=bid, name="A", city_id=city)
    current = datetime.now(UTC) - timedelta(days=1)
    rows = [
        N(id=uuid4(), city_id=city, name="delivery", starts_at=current, amount=Decimal("25")),
        N(
            id=uuid4(),
            city_id=city,
            name=f"delivery:{bid}",
            starts_at=current,
            amount=Decimal("35"),
        ),
    ]

    class Session:
        async def scalars(self, statement):
            return N(all=lambda: rows)

    rates = await delivery_rates(Session(), {bid: branch}, N(id=currency_id, scale=2))
    assert rates[str(bid)]["amount"] == Decimal("35.00")
    rows.append(
        N(id=uuid4(), city_id=city, name=f"delivery:{bid}", starts_at=current, amount=Decimal("40"))
    )
    with pytest.raises(BusinessError, match="Multiple delivery rates"):
        await delivery_rates(Session(), {bid: branch}, N(id=currency_id, scale=2))


@pytest.mark.asyncio
async def test_live_checkout_reuses_one_address_per_city(tmp_path):
    from backend.integrations.telegram.catalog import load_catalog
    from backend.integrations.telegram.live_checkout import execute

    store = Store(tmp_path / "addresses.sqlite3")
    store.catalog = load_catalog()
    restaurants = store.catalog.restaurants[:2]
    basket, slots = [], {}
    for index, restaurant in enumerate(restaurants):
        restaurant.branch_id = f"branch-{index}"
        restaurant.city_id = "same-city"
        slots[restaurant.branch_id] = {"id": f"slot-{index}"}
        for dish in restaurant.menu[:2]:
            basket.append(
                {
                    "selection": f"{restaurant.id}/{dish.id}",
                    "quantity": 1,
                    "option_ids": [],
                    "notes": "",
                }
            )
    with store.db:
        store.save_profile(
            42,
            {
                "basket": basket,
                "fulfillment": "courier",
                "location": {"latitude": 17.3, "longitude": 78.4},
                "branch_slots": slots,
            },
        )

    class Backend:
        tokens = True

        def __init__(self):
            self.addresses = 0
            self.items = []

        async def call(self, method, path, body=None):
            if path == "/carts":
                return {"id": "cart"}
            if path == "/addresses":
                self.addresses += 1
                return {"id": f"address-{self.addresses}"}
            if path.endswith("/items"):
                self.items.append(body)
                return {}
            if path.endswith("/quote"):
                return {
                    "id": "quote",
                    "lines": [],
                    "currency": "INR",
                    "expires_at": "2099-01-01T00:00:00+00:00",
                    "breakdown": {"delivery": "60", "total": "100"},
                }
            return {}

    backend = Backend()
    await execute("quote", 42, store, backend)
    assert backend.addresses == 1 and len(backend.items) == 4
    assert {item["address_id"] for item in backend.items} == {"address-1"}
