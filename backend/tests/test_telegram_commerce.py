import json

import httpx
import pytest

from backend.integrations.telegram.bot import Store, reply
from backend.integrations.telegram.catalog import card, load_catalog, matches
from backend.integrations.telegram.media import render_card
from backend.integrations.telegram.payments import resolve
from backend.tests.test_telegram_bot import message


def test_location_reorder_catalog_and_callbacks(tmp_path):
    store = Store(tmp_path / "bot.sqlite3")
    response = store.process(message(1, "/start"))
    assert "Share GPS" in response["text"]
    response = store.process(message(100, "Share GPS location"))
    assert any(
        button.get("request_location")
        for row in response["reply_markup"]["keyboard"]
        for button in row
    )
    gps = message(2, "")
    gps["message"]["location"] = {"latitude": 17.3, "longitude": 78.4}
    assert "Location saved" in store.process(gps)["text"]
    restaurants = store.process(message(3, "Restaurants"))
    assert len(restaurants["cards"]) == 2
    assert all(c["demo"] for c in restaurants["cards"])
    menu = store.process(message(4, "Menu demo_deccan"))
    assert len(menu["cards"]) == 5
    callback = {
        "update_id": 5,
        "callback_query": {
            "id": "test",
            "from": {"id": 42},
            "data": "Select demo_deccan/chicken",
            "message": {"chat": {"id": 42, "type": "private"}},
        },
    }
    assert "How many" in store.process(callback)["text"]
    for number, text in enumerate(["2", "Delivery", "Use saved location", "Submit request"], 6):
        response = store.process(message(number, text))
    assert "saved" in response["text"]
    saved = json.loads(store.db.execute("SELECT data FROM requests").fetchone()[0])
    assert saved["location"]["latitude"] == 17.3
    assert saved["restaurant"] == "Demo Deccan Kitchen"
    assert "Last request" in store.process(message(10, "/start"))["text"]
    assert "How many" in store.process(message(11, "Order again"))["text"]
    store.process(message(12, "Forget location"))
    assert store.profile(42) == {}
    assert store.profile(99) == {}


def test_budget_vegetarian_comparison_and_artwork():
    catalog = load_catalog()
    chicken = matches(catalog, "chicken biryani under 300")
    assert len(chicken) == 2
    assert all(d.name == "Chicken biryani" for _, d in chicken)
    assert all(d.vegetarian for _, d in matches(catalog, "vegetarian food"))
    assert all(d.vegetarian for _, d in matches(catalog, "without meat under 200"))
    nonveg = matches(catalog, "non-veg biryani")
    assert nonveg and all(not d.vegetarian for _, d in nonveg)
    rows = matches(catalog, "veg biryani under 200")
    assert len(rows) == 2
    assert all(d.vegetarian and d.price_minor <= 20000 for _, d in rows)
    assert rows[0][0].rating >= rows[1][0].rating
    png = render_card(card(rows[0][0], rows[0][1], True))
    assert png.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_payment_ownership_test_only_and_verified_amount(tmp_path, monkeypatch):
    from backend.integrations.telegram import payments

    store = Store(tmp_path / "bot.sqlite3")
    with store.db:
        store.db.execute(
            "INSERT INTO requests(chat,data) VALUES (?,?)",
            (
                42,
                json.dumps(
                    {
                        "item": "Chicken biryani",
                        "quantity": 2,
                        "price_minor": 24900,
                        "demo": True,
                    }
                ),
            ),
        )
    monkeypatch.setattr(payments, "credentials", lambda: ("rzp_test_demo", "secret"))
    calls = []

    def provider(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "payment_links": [
                        {
                            "id": "plink_test",
                            "reference_id": "qb-tg-test-1",
                            "amount": 49800,
                            "amount_paid": 49800,
                            "currency": "INR",
                            "status": "paid",
                        }
                    ]
                },
            )
        raise AssertionError("Existing payment must not create another link")

    payload = {**reply(""), "chat_id": 42, "payment_action": {"request": 1, "kind": "check"}}
    response = await resolve(payload, store, httpx.MockTransport(provider))
    assert "TEST payment verified" in response["text"]
    assert len(calls) == 1

    def wrong_amount(request):
        return httpx.Response(
            200,
            json={
                "payment_links": [
                    {
                        "reference_id": "qb-tg-test-1",
                        "amount": 1,
                        "amount_paid": 1,
                        "currency": "INR",
                        "status": "paid",
                    }
                ]
            },
        )

    mismatch = await resolve(
        {"chat_id": 42, "payment_action": {"request": 1, "kind": "check"}},
        store,
        httpx.MockTransport(wrong_amount),
    )
    assert "uncertain" in mismatch["text"]
    response = await resolve(
        {**reply(""), "chat_id": 99, "payment_action": {"request": 1, "kind": "create"}}, store
    )
    assert "not found" in response["text"]
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_payment_missing_credentials_never_claims_success(tmp_path, monkeypatch):
    from backend.integrations.telegram import payments

    store = Store(tmp_path / "bot.sqlite3")
    store.db.execute(
        "INSERT INTO requests(chat,data) VALUES (?,?)",
        (
            42,
            json.dumps(
                {
                    "quantity": 1,
                    "price_minor": 10000,
                }
            ),
        ),
    )
    monkeypatch.setattr(payments, "credentials", lambda: None)
    result = await resolve(
        {"chat_id": 42, "payment_action": {"request": 1, "kind": "create"}}, store
    )
    assert "not configured" in result["text"]
