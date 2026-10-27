"""Language model proposes a search phrase; menu data remains authoritative."""

import json

import httpx

from backend.integrations.telegram.bot import HOME, ITEMS


async def enrich(update, store):
    store.neural = None
    message = update.get("message", {})
    text = message.get("text", "").strip()
    chat = message.get("chat", {})
    if (
        chat.get("type") != "private"
        or not text
        or text in HOME + ITEMS
        or text
        in (
            "Cart",
            "Checkout",
            "Languages",
            "English",
            "తెలుగు",
            "हिन्दी",
            "Customize",
            "Preparation notes",
            "Add to cart",
            "Favorites",
            "Save favorite",
            "Save restaurant",
            "Order status",
            "Pay live order",
            "Check live payment",
            "More options",
            "Edit customization",
            "Allergens",
            "Meal suggestions",
        )
        or text.startswith(
            (
                "/",
                "Menu ",
                "Select ",
                "Pick ",
                "Qty ",
                "Option ",
                "Slot ",
                "Edit ",
                "Remove ",
                "Set quantity ",
                "Link ",
                "Confirm quote ",
            )
        )
        or text
        in (
            "Biryani",
            "Cancel",
            "Main menu",
            "Pickup",
            "Delivery",
            "Submit request",
            "Use saved location",
        )
        or text.isdigit()
    ):
        return update
    row = store.db.execute("SELECT data FROM sessions WHERE chat=?", (chat["id"],)).fetchone()
    state = json.loads(row[0]) if row else {}
    from backend.integrations.telegram.dialogue_brain import context_for

    memory = context_for(state, store.profile(chat["id"]), getattr(store, "catalog", None))
    if state.get("shopping", {}).get("await_notes"):
        return update
    if state.get("step") not in (None, "food", "item", "search"):
        return update
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "http://127.0.0.1:8766/understand",
                json={
                    "text": text[:500],
                    "previous": state.get("last_query", "")[:500],
                    "context": memory.model_dump(),
                },
            )
            response.raise_for_status()
            result = response.json()
        if result.get("ready"):
            update = {**update, "_query": result.get("query", "")}
            store.neural = result
    except (httpx.HTTPError, ValueError):
        pass
    return update
