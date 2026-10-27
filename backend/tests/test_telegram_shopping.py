from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.integrations.telegram.accounts import Vault
from backend.integrations.telegram.backend_client import BackendError
from backend.integrations.telegram.bot import Store
from backend.integrations.telegram.catalog import Catalog, Dish, Restaurant
from backend.integrations.telegram.conversation import interpret
from backend.integrations.telegram.live_checkout import execute
from backend.tests.test_telegram_bot import message


def test_editable_multiline_basket_localization_favorites_and_typo(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    number = 0

    def send(text):
        nonlocal number
        number += 1
        return store.process(message(number, text))

    send("/start")
    assert len(send("chiken biriyani kavali")["cards"]) == 2
    for text in (
        "Pick demo_deccan/chicken",
        "Qty 2",
        "Add to cart",
        "Pick demo_spice/veg",
        "Qty 1",
        "Preparation notes",
        "less salt",
        "Add to cart",
    ):
        send(text)
    basket = store.profile(42)["basket"]
    assert len(basket) == 2 and basket[1]["notes"] == "less salt"
    assert "× 2" in send("Cart")["text"]
    send("Save favorite")
    assert len(send("Favorites")["cards"]) == 2
    send("Menu demo_deccan")
    send("Save restaurant")
    assert len(send("Favorites")["cards"]) == 3
    send("Edit " + basket[0]["id"])
    send("Set quantity 3")
    assert store.profile(42)["basket"][0]["quantity"] == 3
    send("Edit customization")
    send("Cancel")
    assert len(store.profile(42)["basket"]) == 2
    send("Remove " + basket[1]["id"])
    assert len(store.profile(42)["basket"]) == 1
    send("తెలుగు")
    assert "కార్ట్" in send("Cart")["text"]
    assert send("నాకు చికెన్ బిర్యానీ కావాలి").get("cards")
    assert interpret("for two people")["quantity"] == 2


def test_merchant_options_and_per_restaurant_scheduling(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    windows = [
        {
            "id": str(uuid4()),
            "branch_id": "branch-a",
            "starts_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "ends_at": (datetime.now(UTC) + timedelta(days=1, hours=1)).isoformat(),
        }
    ]
    dish = Dish(
        id="dish",
        name="Paneer",
        price_minor=10000,
        vegetarian=True,
        variant_id=str(uuid4()),
        groups=[
            {
                "id": "g",
                "name": "Spice",
                "minimum": 1,
                "maximum": 1,
                "values": [{"id": str(uuid4()), "name": "Mild", "price_delta": "0.50"}],
            }
        ],
    )
    restaurant = Restaurant(
        id="a", name="A", city="Test", branch_id="branch-a", windows=windows, menu=[dish]
    )
    store.catalog = Catalog(demo=False, restaurants=[restaurant])
    for number, text in enumerate(
        [
            "Pick a/dish",
            "Qty 2",
            "Add to cart",
            "Customize",
            "Option 1",
            "Add to cart",
            "Checkout",
            "Pickup",
            "Slot 1",
        ]
    ):
        response = store.process(message(number, text))
        if number == 2:
            assert "Choose 1–1" in response["text"]
    assert response["live_action"] == "quote"
    profile = store.profile(42)
    assert profile["basket"][0]["options"][0]["name"] == "Mild"
    assert profile["branch_slots"]["branch-a"]["id"] == windows[0]["id"]


def test_pairing_is_one_use_encrypted_and_chat_bound(tmp_path):
    vault = Vault(tmp_path)
    try:
        code = vault.pair({"access_token": "sensitive-token"})
        assert vault.redeem(42, code)
        assert not vault.redeem(99, code)
        assert vault.get(42)["access_token"] == "sensitive-token"
        assert vault.get(99) is None
        raw = vault.db.execute("SELECT value FROM accounts").fetchone()[0]
        assert b"sensitive-token" not in raw
    finally:
        vault.close()


@pytest.mark.asyncio
async def test_payment_waits_for_merchant_acceptance_and_stale_quote_blocks(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    store.catalog = Catalog(demo=False, restaurants=[])
    with store.db:
        store.save_profile(
            42,
            {
                "order_id": "o",
                "basket": [],
                "quote": {
                    "fingerprint": "wrong",
                    "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                },
            },
        )

    class Backend:
        tokens = {"access_token": "test"}

        async def call(self, method, path, body=None, key=None):
            assert path == "/orders/o"
            return {"status": "confirmed"}

        async def pages(self, path):
            return [{"id": "child", "status": "pending"}]

    with pytest.raises(BackendError, match="acceptance"):
        await execute("pay", 42, store, Backend())
    with pytest.raises(BackendError, match="changed"):
        await execute("confirm", 42, store, Backend())
    with pytest.raises(BackendError, match="no longer current"):
        await execute("confirm", 42, store, Backend(), expected_quote="older-quote")


@pytest.mark.asyncio
async def test_voice_requires_confirmation_and_cannot_place_order(tmp_path, monkeypatch):
    from backend.integrations.telegram import runtime, voice

    store = Store(tmp_path / "voice.sqlite3")

    class FakeVault:
        def get(self, chat):
            return None

        def close(self):
            pass

    async def transcribe(voice, telegram):
        return "confirm my order"

    monkeypatch.setattr(runtime, "Vault", FakeVault)
    monkeypatch.setattr(voice, "transcribe", transcribe)
    update = message(1, "")
    update["message"]["voice"] = {"file_id": "test", "duration": 5, "file_size": 500}
    result = await runtime.process(update, store, telegram=object())
    assert "Confirm this transcription" in result["text"]
    assert store.profile(42)["voice_draft"] == "confirm my order"
    assert store.db.execute("SELECT count(*) FROM requests").fetchone()[0] == 0
    result = await runtime.process(message(2, "Discard voice"), store, telegram=object())
    assert "discarded" in result["text"]
    assert "voice_draft" not in store.profile(42)
