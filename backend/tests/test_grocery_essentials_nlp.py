import json

from backend.integrations.telegram.audit_commerce_nlp import CASES
from backend.integrations.telegram.bot import Store
from backend.integrations.telegram.brain_data import build, prompt
from backend.integrations.telegram.catalog import load_catalog
from backend.integrations.telegram.commerce_nlp_data import PRODUCTS, normalize_product_names
from backend.integrations.telegram.conversation import fuzzy_query, interpret
from backend.integrations.telegram.dialogue_brain import (
    Memory,
    grounded_plan,
    parse_plan,
    route_plan,
)
from backend.tests.test_telegram_bot import message


def test_new_commands_cover_both_categories_and_exclude_audit():
    rows, _ = build()
    new = [r for r in rows if r.get("new_v6") and r["split"] == "train"]
    assert len({r["text"] for r in new}) >= 500
    for kind in ("groceries", "essentials"):
        assert (
            len({r["text"] for r in new if PRODUCTS.get(r["target"].split("|")[1]) == kind}) >= 200
        )
    inputs = {r["input"] for r in rows}
    assert all(prompt(text, ctx) not in inputs for ctx, text, _ in CASES)


def test_normalization_does_not_cascade_or_inject_food():
    assert normalize_product_names("dish soap and bath soap") == "dishwashing liquid and bath soap"
    assert normalize_product_names("biyyam and doodh") == "rice and milk"
    query = interpret(
        "detergent under 300", {"confidence": 0.99, "structured": "search|chicken biryani|2|300|"}
    )["query"]
    assert "biryani" not in query
    assert "price" in fuzzy_query("price of rice", load_catalog())


def test_grounding_supports_counts_not_silent_weight_conversion():
    memory = Memory(dish="detergent", quantity=2, budget=500)
    doubled = grounded_plan(
        parse_plan("search|detergent|4|500|||show_matches", 0.99, memory), "double my packs", memory
    )
    assert doubled.quantity == 4
    assert (
        grounded_plan(
            parse_plan("search|detergent|6|500|||show_matches", 0.99, memory),
            "double my packs",
            memory,
        )
        is None
    )
    assert (
        grounded_plan(
            parse_plan("search|rice|2||||show_matches", 0.99, Memory()),
            "I need 2 kg rice",
            Memory(),
        ).step
        == "ask_pack"
    )
    assert route_plan(parse_plan("essentials||||||open_screen", 0.99, Memory())) == "Essentials"


def test_grocery_then_followup_and_essentials_are_grounded_in_store(tmp_path):
    store = Store(tmp_path / "grocery.sqlite3")
    for index, (text, raw) in enumerate(
        (
            ("I need 2 packs of rice under 200", "search|rice|2|200|||show_matches"),
            ("same item, budget 150, cheaper please", "search|rice|2|150||price|show_matches"),
            ("switch to detergent under 450", "search|detergent|2|450||price|show_matches"),
        ),
        1,
    ):
        memory = (
            Memory.model_validate(
                json.loads(
                    store.db.execute("SELECT data FROM sessions WHERE chat=42").fetchone()[0]
                ).get("brain_memory", {})
            )
            if index > 1
            else Memory()
        )
        plan = grounded_plan(parse_plan(raw, 0.99, memory), text, memory)
        store.neural = {"plan": plan.model_dump()}
        reply = store.process(message(index, text))
        assert reply["cards"] and all("biryani" not in c["title"].lower() for c in reply["cards"])
        assert all(
            c["kind"] == ("essentials" if index == 3 else "groceries") for c in reply["cards"]
        )
        if index == 2:
            assert reply["cards"][0]["price_minor"] == 6200
    assert not store.db.execute("SELECT count(*) FROM requests").fetchone()[0]


def test_pack_question_shows_choices_without_applying_kg_as_quantity(tmp_path):
    store = Store(tmp_path / "packs.sqlite3")
    store.neural = {"plan": parse_plan("clarify|rice|||||ask_pack", 0.99, Memory()).model_dump()}
    reply = store.process(message(1, "rice 2 kg"))
    assert "pack size" in reply["text"] and reply["cards"]
    assert not store.profile(42).get("basket")


def test_primary_planner_does_not_call_food_only_fallback(monkeypatch):
    from backend.integrations.telegram import language_server as server

    class Legacy:
        def generate(self, *args, **kwargs):
            raise AssertionError("food-only fallback must not run for an accepted planner input")

    class Brain:
        metadata = {"architecture": "test-generic-planner"}

        def accepts(self, text):
            return True

        def generate(self, text):
            return "search|milk|2|160|||show_matches", 0.99

    monkeypatch.setattr(server, "model", Legacy())
    monkeypatch.setattr(server, "trained", Legacy())
    monkeypatch.setattr(server, "brain", Brain())
    result = server.understand(server.Query(text="milk 2 packs under 160"))
    assert result["plan"]["dish"] == "milk" and result["query"] == "milk"
    assert result["structured"] == ""


def test_grocery_budget_covers_all_requested_packs(tmp_path):
    store = Store(tmp_path / "budget.sqlite3")
    store.neural = {
        "plan": parse_plan("search|milk|3|100|||show_matches", 0.99, Memory()).model_dump()
    }
    reply = store.process(message(1, "3 packs of milk under 100"))
    assert not reply.get("cards")


def test_new_followup_text_requires_product_memory():
    rows, _ = build()
    targets = {
        r["target"]
        for r in rows
        if r.get("new_v6") and r["text"] == "make that 5 packs" and r["split"] == "train"
    }
    assert len(targets) >= 28


def test_selected_pack_names_keep_product_memory_for_editing():
    from backend.integrations.telegram.dialogue_brain import context_for

    memory = context_for(
        {"shopping": {"selection": "demo_market/rice", "quantity": 2}}, {}, load_catalog()
    )
    assert memory.dish == "rice" and memory.quantity == 2 and memory.stage == "customize"
