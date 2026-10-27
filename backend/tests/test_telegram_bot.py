from backend.integrations.telegram.bot import Store


def message(number, text, chat=42, kind="private"):
    return {
        "update_id": number,
        "message": {"chat": {"id": chat, "type": kind}, "from": {"id": chat}, "text": text},
    }


def test_delivery_request_is_durable_and_submission_is_idempotent(tmp_path):
    path = tmp_path / "bot.sqlite3"
    store = Store(path)
    choices = [
        "/start",
        "Food",
        "Biryani",
        "Select demo_deccan/chicken",
        "2",
        "Delivery",
        "10 Example Street, Hyderabad",
    ]
    for number, text in enumerate(choices):
        response = store.process(message(number, text))
    assert "Review request" in response["text"]
    store.db.close()
    store = Store(path)
    update = message(10, "Submit request")
    response = store.process(update)
    assert "QB-TG-000001" in response["text"]
    assert "not a confirmed order" in response["text"]
    assert store.process(update) == response
    store.process(message(11, "Submit request"))
    assert store.db.execute("SELECT count(*) FROM requests").fetchone()[0] == 1
    assert "Chicken biryani x2" in store.process(message(12, "My requests"))["text"]
    assert "no requests" in store.process(message(13, "My requests", chat=99))["text"]


def test_cancel_invalid_input_and_groups(tmp_path):
    store = Store(tmp_path / "bot.sqlite3")
    assert store.process(message(0, "/start", kind="group")) is None
    for number, text in enumerate(
        [
            "Food",
            "Biryani",
            "Select demo_deccan/veg",
            "100",
            "2",
            "Delivery",
            "short",
            "/cancel",
            "Submit request",
        ],
        start=1,
    ):
        response = store.process(message(number, text))
        if text == "short":
            assert "10–500" in response["text"]
    assert store.db.execute("SELECT count(*) FROM requests").fetchone()[0] == 0


def test_pickup_and_unavailable_category(tmp_path):
    store = Store(tmp_path / "bot.sqlite3")
    assert store.process(message(0, "Groceries"))["cards"]
    for number, text in enumerate(
        ["Food", "Biryani", "Select demo_spice/egg", "1", "Pickup", "Submit request"], start=1
    ):
        response = store.process(message(number, text))
    assert "saved" in response["text"]
