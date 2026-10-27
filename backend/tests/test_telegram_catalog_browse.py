import json

from backend.integrations.telegram.bot import HOME, Store
from backend.integrations.telegram.catalog import Catalog
from backend.tests.test_telegram_bot import message


def test_browse_food_groceries_and_all_with_card_details(tmp_path):
    store = Store(tmp_path / "browse.sqlite3")
    for index, name in enumerate(("Food", "Groceries", "All items"), 1):
        result = store.process(message(index, name))
        cards = result["cards"]
        assert cards and all(c["merchant"] and c["price_minor"] > 0 for c in cards)
        assert all("image_url" in c and "action" in c for c in cards)
        if name != "All items":
            assert all(c["kind"] == name.lower() for c in cards)
        else:
            state = json.loads(
                store.db.execute("SELECT data FROM sessions WHERE chat=42").fetchone()[0]
            )
            assert {c["kind"] for c in state["result_cards"]} == {"food", "groceries", "essentials"}
            assert result["next_page"] == "Page 6"


def test_medicine_not_sold_or_listed(tmp_path):
    assert "Medicines" not in HOME
    store = Store(tmp_path / "blocked.sqlite3")
    assert "do not sell medicines" in store.process(message(1, "Medicines"))["text"]
    catalog = Catalog.model_validate(
        {
            "restaurants": [
                {
                    "id": "store",
                    "name": "Store",
                    "city": "City",
                    "menu": [
                        {
                            "id": "drug",
                            "name": "Medicine",
                            "kind": "medicines",
                            "price_minor": 1000,
                        },
                        {"id": "rice", "name": "Rice", "kind": "groceries", "price_minor": 2000},
                    ],
                }
            ]
        }
    )
    assert [d.id for _, d in catalog.rows()] == ["rice"]


def test_grocery_fallback_is_a_real_image():
    from backend.integrations.telegram.catalog import card, load_catalog
    from backend.integrations.telegram.media import render_card

    restaurant, dish = next((r, d) for r, d in load_catalog().rows() if d.kind == "groceries")
    item = card(restaurant, dish)
    assert "Store:" in item["text"] and "per 1 kg" in item["text"]
    assert render_card(item).startswith(b"\x89PNG\r\n\x1a\n")


def test_live_catalog_blocks_pharmacies_and_preserves_product_photos():
    import asyncio

    from backend.integrations.telegram.backend_client import Backend

    rows = [
        {
            "branch_id": kind,
            "merchant_type": kind,
            "category_name": "Products",
            "currency": "INR",
            "branch_name": kind.title(),
            "variant_id": kind,
            "category_id": "category",
            "name": "Product",
            "variant_name": "Standard",
            "unit_price": "12.50",
            "available_quantity": 10,
            "unit": "1 kg",
            "image_url": "https://example.com/product.jpg",
        }
        for kind in ("food", "grocery", "pharmacy")
    ]

    async def pages(path):
        if path.startswith("/channel/catalog"):
            return rows
        if path == "/merchants/branches":
            return [{"id": r["branch_id"], "city_id": "city"} for r in rows]
        return [{"reserved": 0, "capacity": 10, "starts_at": "2099-01-01T10:00:00+00:00"}]

    backend = Backend.__new__(Backend)
    backend.pages = pages
    catalog = asyncio.run(backend.catalog())
    assert {d.kind for _, d in catalog.rows()} == {"food", "groceries"}
    assert all(
        d.price_minor == 1250 and str(d.image_url) == "https://example.com/product.jpg"
        for _, d in catalog.rows()
    )
