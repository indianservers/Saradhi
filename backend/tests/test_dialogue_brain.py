from backend.integrations.telegram.bot import Store
from backend.integrations.telegram.brain_data import build, prompt, training_source
from backend.integrations.telegram.dialogue_brain import (
    Memory,
    grounded_plan,
    parse_plan,
    route_plan,
    search_query,
)
from backend.tests.test_telegram_bot import message


def test_new_training_commands_and_no_audit_leakage():
    from backend.integrations.telegram.audit_brain import CASES
    from backend.integrations.telegram.audit_brain_v2 import CASES as fresh_cases

    rows, count = build()
    assert len({r["text"] for r in rows if r.get("new_v2") and r["split"] == "train"}) >= 500
    assert len({r["text"] for r in rows if r.get("new_v3") and r["split"] == "train"}) >= 500
    assert len({r["text"] for r in rows if r.get("new_v4") and r["split"] == "train"}) >= 200
    assert len({r["text"] for r in rows if r.get("new_v5") and r["split"] == "train"}) >= 100
    assert count >= 200
    assert len({r["text"] for r in rows if r["new"] and r["split"] == "train"}) >= 200
    training = {r["input"] for r in rows if r["split"] == "train"}
    assert training.isdisjoint({r["input"] for r in rows if r["split"] != "train"})
    assert {r["text"].lower() for r in rows if r.get("new_v3")}.isdisjoint(
        {r["text"].lower() for r in rows if not r.get("new_v3")}
    )
    assert not any(prompt(text, context) in training for context, text, _ in CASES + fresh_cases)
    first = {"text": "same dish", "input": prompt("same dish", {"dish": "paneer"})}
    second = {"text": "same dish", "input": prompt("same dish", {"dish": "masala dosa"})}
    assert training_source(first) != training_source(second)
    assert training_source({"text": "hello"}) == "hello"


def test_memory_resolves_changes_and_blocks_invented_numbers():
    memory = Memory(dish="chicken biryani", quantity=2, budget=400, stage="search")
    plan = grounded_plan(
        parse_plan("search|chicken biryani|4|400|||show_matches", 0.98, memory),
        "make that 4 portions",
        memory,
    )
    assert plan.quantity == 4 and plan.budget == 400
    assert (
        grounded_plan(
            parse_plan("search|chicken biryani|8|400|||show_matches", 0.99, memory),
            "something cheaper",
            memory,
        )
        is None
    )
    price = grounded_plan(parse_plan("cheaper||||||open_screen", 0.99, memory), "cheaper", memory)
    assert price.dish == memory.dish and price.sort == "price"
    assert "cheapest" in search_query(price)
    missing = parse_plan("cheaper||||||open_screen", 0.99, Memory())
    assert missing.action == "clarify"
    assert parse_plan("run_shell|delete data", 1, memory) is None
    confirm = parse_plan("confirm||||||open_screen", 0.99, memory)
    assert route_plan(confirm) == "Checkout"


def test_neural_plan_drives_contextual_discovery_without_submitting(tmp_path):
    store = Store(tmp_path / "dialogue.sqlite3")
    store.neural = {
        "plan": {
            "action": "search",
            "dish": "chicken biryani",
            "quantity": 2,
            "budget": 300,
            "diet": "",
            "sort": "price",
            "stage": "search",
            "step": "show_matches",
            "confidence": 0.99,
        }
    }
    # A legacy decoder hallucination must not override the contextual plan.
    store.neural["structured"] = "search|paneer|2|400|"
    store.neural["confidence"] = 0.99
    result = store.process(message(1, "keep those under 300"))
    assert len(result["cards"]) == 2
    assert result["cards"][0]["text"].find("219.00") >= 0
    import json

    state = json.loads(store.db.execute("SELECT data FROM sessions WHERE chat=42").fetchone()[0])
    assert state["brain_memory"]["dish"] == "chicken biryani"
    assert state["suggested_quantity"] == 2
    assert store.db.execute("SELECT count(*) FROM requests").fetchone()[0] == 0
    store.neural = {
        "plan": {
            "action": "clarify",
            "dish": "",
            "quantity": None,
            "budget": None,
            "diet": "",
            "sort": "",
            "stage": "",
            "step": "ask_dish",
            "confidence": 0.99,
        }
    }
    assert "Which dish" in store.process(message(2, "that one"))["text"]


def test_unevaluated_or_changed_weights_do_not_replace_running_brain(tmp_path, monkeypatch):
    import json

    from backend.integrations.telegram import language_server

    monkeypatch.setattr(language_server, "LOCAL_MODEL", tmp_path / "flan")
    existing = object()
    monkeypatch.setattr(language_server, "brain", existing)
    assert language_server.load_brain() is False
    folder = tmp_path / "quickbuddy-brain"
    folder.mkdir()
    (folder / "deployment.json").write_text(json.dumps({"model_sha256": "wrong"}))
    (folder / "model.keras").write_bytes(b"changed weights")
    assert language_server.load_brain() is False
    assert language_server.brain is existing


def test_generated_dish_requires_message_or_memory_evidence():
    for phrase in ("help with dinner", "show my basket", "surprise me"):
        p = grounded_plan(
            parse_plan("search|masala dosa|||||show_matches", 0.99, Memory()), phrase, Memory()
        )
        assert p.action == "clarify" and p.step == "ask_dish"
    p = grounded_plan(
        parse_plan("search|chicken biryani|||||show_matches", 0.99, Memory()),
        "chiken biryani please",
        Memory(),
    )
    assert p.action == "search"


def test_compound_plan_and_replacement_keep_other_fields(tmp_path):
    import json

    store = Store(tmp_path / "compound.sqlite3")
    for update_id, text, dish, quantity, budget in (
        (
            1,
            "Keep chicken biryani; set portions 5 and spending limit 860",
            "chicken biryani",
            5,
            860,
        ),
        (
            2,
            "Drop chicken biryani; I want veg biryani while keeping the portions and budget",
            "veg biryani",
            5,
            860,
        ),
    ):
        plan = parse_plan(f"search|{dish}|{quantity}|{budget}||price|show_matches", 0.99, Memory())
        store.neural = {"plan": plan.model_dump()}
        result = store.process(message(update_id, text))
        assert result["cards"] and all(dish in card["title"].lower() for card in result["cards"])
        state = json.loads(
            store.db.execute("SELECT data FROM sessions WHERE chat=42").fetchone()[0]
        )
        assert state["brain_memory"]["dish"] == dish
        assert state["brain_memory"]["quantity"] == quantity
        assert state["brain_memory"]["budget"] == budget
        assert not store.db.execute("SELECT count(*) FROM requests").fetchone()[0]


def test_joint_diet_quantity_budget_plan_is_grounded():
    memory = Memory(dish="chicken biryani", quantity=1, budget=400, sort="price")
    plan = grounded_plan(
        parse_plan("search|chicken biryani|4|680|vegetarian|price|show_matches", 0.99, memory),
        "Update chicken biryani: vegetarian only, 4 portions, limit 680",
        memory,
    )
    assert (plan.quantity, plan.budget, plan.diet, plan.sort) == (4, 680, "vegetarian", "price")
    query = search_query(plan)
    assert "chicken" not in query and "vegetarian" in query and "under 680" in query


def test_diet_change_does_not_restore_old_meat_search_terms(tmp_path):
    store = Store(tmp_path / "diet.sqlite3")
    for index, diet in enumerate(("", "vegetarian"), 1):
        plan = parse_plan(f"search|chicken biryani|4|680|{diet}||show_matches", 0.99, Memory())
        store.neural = {"plan": plan.model_dump()}
        reply = store.process(
            message(index, "chicken biryani" if not diet else "vegetarian alternatives")
        )
    assert reply["cards"] and all("veg biryani" in c["title"].lower() for c in reply["cards"])


def test_latest_budget_phrase_has_different_targets_for_different_memory():
    rows, _ = build()
    phrases = {}
    for row in rows:
        if row.get("new_v5") and row["split"] == "train":
            phrases.setdefault(row["text"], set()).add(row["target"])
    assert len(phrases) >= 100
    assert all(len(targets) == 4 for targets in phrases.values())
