"""Local Telegram request intake. Run with python -m backend.integrations.telegram.bot."""

import asyncio
import json
import logging
import os
import re
import sqlite3
from pathlib import Path

import httpx

from backend.integrations.telegram.catalog import card, load_catalog, matches

ROOT = Path(__file__).resolve().parents[3]
HOME = [
    "Food",
    "Groceries",
    "Essentials",
    "All items",
    "Stores",
    "Restaurants",
    "Search dishes",
    "Order again",
    "Share GPS location",
    "Forget location",
    "My requests",
    "Payment",
    "Help",
]
ITEMS = ["Chicken biryani", "Mutton biryani", "Veg biryani", "Egg biryani"]
LOG = logging.getLogger("quickbuddy.telegram")


def reply(text, buttons=None):
    buttons = buttons or ["Main menu"]
    keyboard = [
        {"text": value, **({"request_location": True} if value == "Share GPS location" else {})}
        for value in buttons
    ]
    return {
        "text": text,
        "reply_markup": {
            "keyboard": [keyboard[index : index + 2] for index in range(0, len(keyboard), 2)],
            "resize_keyboard": True,
        },
    }


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions(chat INTEGER PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests(
                id INTEGER PRIMARY KEY, chat INTEGER NOT NULL, data TEXT NOT NULL,
                created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS updates(id INTEGER PRIMARY KEY, response TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY, chat INTEGER NOT NULL, direction TEXT NOT NULL,
                text TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS profiles(chat INTEGER PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS test_payments(
                request INTEGER PRIMARY KEY, chat INTEGER NOT NULL, data TEXT NOT NULL);
        """)

    def process(self, update):
        callback = update.get("callback_query")
        message = update.get("message", {})
        if callback:
            message = {
                **callback.get("message", {}),
                "text": callback.get("data", ""),
                "from": callback.get("from", {}),
            }
        chat = message.get("chat", {})
        if chat.get("type") != "private" or message.get("from", {}).get("is_bot"):
            return None
        with self.db:
            previous = self.db.execute(
                "SELECT response FROM updates WHERE id=?", (update["update_id"],)
            ).fetchone()
            if previous:
                return json.loads(previous[0])
            chat_id = chat["id"]
            row = self.db.execute("SELECT data FROM sessions WHERE chat=?", (chat_id,)).fetchone()
            state = json.loads(row[0]) if row else {}
            text = message.get("text", "").strip()
            location = message.get("location")
            if location is not None:
                lat, lon = location.get("latitude"), location.get("longitude")
                if (
                    isinstance(lat, (int, float))
                    and isinstance(lon, (int, float))
                    and -90 <= lat <= 90
                    and -180 <= lon <= 180
                ):
                    profile = self.profile(chat_id)
                    profile.pop("address", None)
                    profile["location"] = {"latitude": lat, "longitude": lon}
                    self.save_profile(chat_id, profile)
                    text = "[GPS location shared]"
                    if state.get("step") == "address":
                        state.update(
                            location=profile["location"],
                            address="Shared GPS location",
                            step="confirm",
                        )
                        response = self.review(state)
                    else:
                        response = reply(
                            "📍 Location saved for your next request. "
                            "You can change or forget it anytime. "
                            "Coverage will be confirmed separately.",
                            HOME,
                        )
                else:
                    response = reply("That location is invalid. Please share your GPS again.")
            else:
                self.query_hint = update.get("_query", "")
                response = self.route(chat_id, text, state)
            if len(response.get("cards", [])) > 6:
                state["result_cards"] = response["cards"]
                response["cards"] = response["cards"][:6]
                response["next_page"] = "Page 6"
            self.db.execute(
                "INSERT INTO events(chat,direction,text) VALUES (?,?,?)",
                (chat_id, "customer", text),
            )
            self.db.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?,?)", (chat_id, json.dumps(state))
            )
            response["chat_id"] = chat_id
            self.db.execute(
                "INSERT INTO updates VALUES (?,?)", (update["update_id"], json.dumps(response))
            )
            return response

    def profile(self, chat):
        row = self.db.execute("SELECT data FROM profiles WHERE chat=?", (chat,)).fetchone()
        return json.loads(row[0]) if row else {}

    def save_profile(self, chat, profile):
        self.db.execute("INSERT OR REPLACE INTO profiles VALUES (?,?)", (chat, json.dumps(profile)))

    def catalog_response(self, text, cards):
        response = reply(text, HOME)
        response["cards"] = cards
        return response

    def route(self, chat, text, state):
        if re.search(r"\b(medicines?|pharmacy|pharmaceuticals?)\b", text, re.I):
            return reply(
                "We do not sell medicines. Browse Food or Groceries.",
                ["Food", "Groceries", "All items", "Main menu"],
            )
        from backend.integrations.telegram.shopping import Shopping

        shopping = Shopping(self).route(chat, text, state)
        if shopping is not None:
            return shopping
        if text in ("/start", "/menu", "Main menu", "/cancel", "Cancel"):
            state.clear()
            profile = self.profile(chat)
            latest = self.db.execute(
                "SELECT data FROM requests WHERE chat=? ORDER BY id DESC LIMIT 1", (chat,)
            ).fetchone()
            returning = ""
            if latest:
                returning = f"\nLast request: {json.loads(latest[0])['item']}. Tap Order again."
            location_note = (
                "\n📍 Using your saved location/address."
                if profile
                else "\n📍 New here? Share GPS or enter address at checkout."
            )
            return reply(
                "🍽 Welcome to Quickbuddy! Browse restaurants or tell me what you crave.\n"
                "Try: chicken biryani under 300, or vegetarian food."
                + returning
                + location_note
                + "\nPilot: requests await merchant confirmation.",
                HOME,
            )
        if text in ("/help", "Help"):
            return reply(
                "Browse Restaurants for full menus, or type a dish, budget "
                "or vegetarian preference. "
                "Share GPS to save your location; Order again repeats a previous selection. "
                "/menu opens services; /cancel clears the draft. Payment is Razorpay TEST only. "
                "Requests await merchant confirmation; no delivery is promised."
            )
        if text == "Forget location":
            profile = self.profile(chat)
            for key in ("location", "address", "quote"):
                profile.pop(key, None)
            self.save_profile(chat, profile)
            state.clear()
            return reply(
                "Saved location/address forgotten. Previous request records are retained.", HOME
            )
        if text == "Share GPS location":
            return reply(
                "📍 Tap Share GPS location in Telegram to share your current position. "
                "We store it for future requests. Use Forget location to remove it.",
                ["Share GPS location", "Main menu"],
            )
        if text == "Payment":
            latest = self.db.execute(
                "SELECT id FROM requests WHERE chat=? ORDER BY id DESC LIMIT 1", (chat,)
            ).fetchone()
            return reply(
                "🧪 Razorpay TEST checkout. No real money or delivery. "
                "Select your latest request to test payment.",
                [f"Pay request {latest[0]}", "Main menu"] if latest else HOME,
            )
        payment_match = re.fullmatch(r"(Pay request|Check payment) (\d+)", text)
        if payment_match:
            response = reply("Checking Razorpay TEST checkout…")
            response["payment_action"] = {
                "kind": "check" if payment_match[1] == "Check payment" else "create",
                "request": int(payment_match[2]),
            }
            return response
        if text == "Use saved location":
            profile = self.profile(chat)
            if state.get("step") == "address" and profile:
                state.update(address=profile.get("address", "Shared GPS location"), step="confirm")
                if profile.get("location"):
                    state["location"] = profile["location"]
                return self.review(state)
            return reply("No saved location available. Share GPS or enter an address.")
        if text == "Order again":
            latest = self.db.execute(
                "SELECT data FROM requests WHERE chat=? ORDER BY id DESC LIMIT 1", (chat,)
            ).fetchone()
            if not latest:
                return reply("No previous requests yet. Browse Restaurants to begin.", HOME)
            previous = json.loads(latest[0])
            if previous.get("selection"):
                return self.route(chat, "Select " + previous["selection"], state)
            state.clear()
            state.update(item=previous["item"], step="quantity")
            return reply(
                f"Repeat {previous['item']}? Choose quantity to review a new request.",
                ["1", "2", "3", "4", "5", "Cancel"],
            )
        catalog = getattr(self, "catalog", None) or load_catalog()
        demo = "🧪 DEMO catalog · sample prices & synthetic ratings\n" if catalog.demo else ""
        if text in ("Restaurants", "Food"):
            state["step"] = "food"
            response = self.catalog_response(
                demo + "🏪 Choose a restaurant to see its full menu, or type a dish to compare.",
                [card(r, demo=catalog.demo) for r in catalog.restaurants],
            )
            response["reply_markup"] = reply(
                "", ["Biryani", "Restaurants", "Search dishes", "Share GPS location", "Main menu"]
            )["reply_markup"]
            return response
        if text.startswith("Menu "):
            restaurant = next((r for r in catalog.restaurants if r.id == text[5:]), None)
            if restaurant:
                return self.catalog_response(
                    demo + f"🍴 Full menu · {restaurant.name}",
                    [card(restaurant, d, catalog.demo) for d in restaurant.menu],
                )
            return reply("Restaurant no longer available. Open Restaurants again.")
        if text.startswith("Select "):
            selection = text[7:]
            chosen = next(
                ((r, d) for r, d in catalog.rows() if f"{r.id}/{d.id}" == selection), None
            )
            if chosen:
                restaurant, dish = chosen
                state.clear()
                state.update(
                    item=dish.name,
                    restaurant=restaurant.name,
                    selection=selection,
                    price_minor=dish.price_minor,
                    demo=catalog.demo,
                    step="quantity",
                )
                return reply(
                    f"{dish.name} · {restaurant.name}\n"
                    f"₹{dish.price_minor / 100:.2f} per portion"
                    + (" · DEMO price" if catalog.demo else " · subject to confirmation")
                    + "\nHow many portions?",
                    ["1", "2", "3", "4", "5", "Cancel"],
                )
            return reply("This item is no longer available. Search again.")
        if text == "Search dishes":
            state["step"] = "search"
            return reply(
                "What would you like? Try ‘veg biryani under 200’. "
                "You can also type a restaurant name.",
                ["Restaurants", "Main menu"],
            )
        if text.startswith("Page "):
            index = int(text[5:]) if text[5:].isdigit() else 0
            allowed = {f"{r.id}/{d.id}" for r, d in catalog.rows()}
            stores = {r.id for r in catalog.restaurants}
            cards = [
                c
                for c in state.get("result_cards", [])
                if (c["action"].startswith("Menu ") and c["action"][5:] in stores)
                or (
                    c["action"].startswith(("Pick ", "Select "))
                    and c["action"].split(" ", 1)[1] in allowed
                )
            ]
            response = self.catalog_response("More menu choices", cards[index : index + 6])
            if index + 6 < len(cards):
                response["next_page"] = f"Page {index + 6}"
            return response
        if text == "My requests":
            rows = self.db.execute(
                "SELECT id,data FROM requests WHERE chat=? ORDER BY id DESC LIMIT 5", (chat,)
            ).fetchall()
            lines = [
                f"QB-TG-{number:06d}: {json.loads(data)['item']} "
                f"x{json.loads(data)['quantity']} — awaiting merchant confirmation"
                for number, data in rows
            ]
            return reply(
                "Your latest requests:\n" + "\n".join(lines)
                if lines
                else "You have no requests yet."
            )
        if text in ("Food", "Groceries", "Essentials"):
            state.clear()
            if text == "Food":
                state["step"] = "food"
                return reply(
                    "Choose food. Biryani is available for pilot requests.",
                    ["Biryani", "Main menu"],
                )
            return reply(f"{text} menu is coming soon. Try Food → Biryani.")
        step = state.get("step")
        if text == "Biryani" and step in (None, "food"):
            if not catalog.restaurants:
                return reply(
                    "No live dishes available. Link a customer account "
                    "and check the merchant catalog."
                )
            state["step"] = "item"
            response = reply(
                "Choose your biryani. Availability and price will be confirmed later.",
                ITEMS + ["Main menu"],
            )
            response["cards"] = [card(r, d, catalog.demo) for r, d in matches(catalog, "biryani")]
            response["text"] = demo + "🍚 Biryani across restaurants. Compare prices and ratings."
            return response
        if step == "item" and text in ITEMS:
            state.update(item=text, step="quantity")
            return reply("How many portions?", ["1", "2", "3", "4", "5", "Cancel"])
        if step == "quantity" and text in ("1", "2", "3", "4", "5"):
            state.update(quantity=int(text), step="method")
            return reply(
                "Choose your preferred fulfillment method.", ["Pickup", "Delivery", "Cancel"]
            )
        if step == "method" and text in ("Pickup", "Delivery"):
            state["method"] = text
            if text == "Delivery":
                state["step"] = "address"
                return reply(
                    "Type your delivery address (10–500 characters). "
                    "It will be stored locally with this request. "
                    "Delivery availability is confirmed later.",
                    (["Use saved location"] if self.profile(chat) else [])
                    + ["Share GPS location", "Cancel"],
                )
            state["step"] = "confirm"
            return self.review(state)
        if step == "address" and 10 <= len(text) <= 500:
            state.update(address=text, step="confirm")
            self.save_profile(chat, {**self.profile(chat), "address": text})
            return self.review(state)
        if step == "confirm" and text == "Submit request":
            data = {key: value for key, value in state.items() if key != "step"}
            cursor = self.db.execute(
                "INSERT INTO requests(chat,data) VALUES (?,?)", (chat, json.dumps(data))
            )
            state.clear()
            return reply(
                f"Request QB-TG-{cursor.lastrowid:06d} saved.\n"
                "Awaiting merchant confirmation. No payment collected; "
                "this is not a confirmed order.",
                [f"Pay request {cursor.lastrowid}", "My requests", "Main menu"],
            )
        if step == "address":
            return reply("Please type an address of 10–500 characters.", ["Cancel"])
        if step in ("quantity", "method", "confirm"):
            return reply(
                "Please complete or cancel your current selection.", ["Cancel", "Main menu"]
            )
        if text:
            query = text
            # Explicit constraints always come from customer text, never model guesses.
            hint = getattr(self, "query_hint", "")
            if hint and not matches(catalog, text):
                query = hint + " " + text
            if (
                state.get("last_query")
                and re.search(
                    r"\b(cheaper|under|below|same|that|it|vegetarian|veg)\b", text.lower()
                )
                and not any(d.name.lower() in text.lower() for _, d in catalog.rows())
            ):
                prior = re.sub(r"(?:under|below)\s*\d+", "", state["last_query"])
                query = prior + " " + query
            rows = matches(catalog, query)
            if rows:
                response = self.catalog_response(
                    demo + f"🍽 Matches for “{text[:100]}” · choose a restaurant's item.\n"
                    "Ratings are shown with their source. Coverage is not yet verified.",
                    [card(r, d, catalog.demo) for r, d in rows],
                )
                state["last_query"] = query[:500]
                if len(response["cards"]) > 6:
                    state["result_cards"] = response["cards"]
                    response["cards"] = response["cards"][:6]
                    response["next_page"] = "Page 6"
                return response
        return reply("Tell me a dish or restaurant, or browse the menu.", HOME)

    @staticmethod
    def review(state):
        return reply(
            f"Review request\n{state['item']} × {state['quantity']}\n"
            + (
                f"{state['restaurant']}\nSubtotal: ₹"
                f"{state['price_minor'] * state['quantity'] / 100:.2f}"
                + (" · DEMO\n" if state.get("demo") else " · before confirmed fees\n")
                if state.get("restaurant")
                else ""
            )
            + f"Preference: {state['method']}\n"
            + (f"Address: {state['address']}\n" if state.get("address") else "")
            + "Price, availability and timing: awaiting merchant confirmation.\n"
            "No payment will be taken.",
            ["Submit request", "Cancel"],
        )


class TelegramError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"Telegram request failed (HTTP {status})")


class Telegram:
    def __init__(self, token):
        self.base = f"https://api.telegram.org/bot{token}/"
        self.client = httpx.AsyncClient(timeout=40)

    async def call(self, method, **payload):
        response = await self.client.post(self.base + method, json=payload)
        if response.status_code != 200:
            raise TelegramError(response.status_code)
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method} failed")
        return data["result"]

    async def send_text(self, chat, text, markup=None):
        for start in range(0, max(1, len(text)), 3800):
            payload = {"chat_id": chat, "text": text[start : start + 3800] or "Choose an option."}
            if markup and start + 3800 >= len(text):
                payload["reply_markup"] = markup
            await self.call("sendMessage", **payload)

    async def deliver(self, result):
        from backend.integrations.telegram.media import render_card

        payload = {
            key: value
            for key, value in result.items()
            if key not in ("cards", "next_page", "checkout_url", "nlp")
        }
        if result.get("checkout_url"):
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [
                        {
                            "text": "Open Razorpay TEST checkout ↗",
                            "url": result["checkout_url"],
                        }
                    ]
                ]
            }
        await self.send_text(payload["chat_id"], payload["text"], payload.get("reply_markup"))
        for item in result.get("cards", [])[:6]:
            caption = (
                "🧪 DEMO · Sample data\n" if item["demo"] else ""
            ) + f"🍽 {item['title']}\n{item['text']}"
            markup = {
                "inline_keyboard": [
                    [
                        {
                            "text": item["label"],
                            "callback_data": item["action"],
                        }
                    ]
                ]
            }
            short_caption = (
                caption if len(caption) <= 1024 else item["title"] + "\nFull details follow."
            )
            if item.get("image_url"):
                try:
                    await self.call(
                        "sendPhoto",
                        chat_id=result["chat_id"],
                        photo=item["image_url"],
                        caption=short_caption,
                        reply_markup=markup,
                    )
                    if len(caption) > 1024:
                        await self.send_text(result["chat_id"], caption)
                    continue
                except RuntimeError:
                    pass
            try:
                response = await self.client.post(
                    self.base + "sendPhoto",
                    data={
                        "chat_id": str(result["chat_id"]),
                        "caption": short_caption,
                        "reply_markup": json.dumps(markup),
                    },
                    files={"photo": ("menu-card.png", render_card(item), "image/png")},
                )
                if response.status_code != 200 or not response.json().get("ok"):
                    raise RuntimeError("Card image unavailable")
                if len(caption) > 1024:
                    await self.send_text(result["chat_id"], caption)
            except (RuntimeError, ValueError):
                await self.send_text(result["chat_id"], caption, markup)
        if result.get("next_page"):
            await self.call(
                "sendMessage",
                chat_id=result["chat_id"],
                text="More choices available",
                reply_markup={
                    "inline_keyboard": [
                        [
                            {
                                "text": "More results →",
                                "callback_data": result["next_page"],
                            }
                        ]
                    ]
                },
            )


async def main():
    from dotenv import dotenv_values

    from backend.integrations.telegram.payments import resolve
    from backend.integrations.telegram.runtime import process

    config = dotenv_values(ROOT / ".secrets" / "telegram.env")
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or config.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN or .secrets/telegram.env first.")
    local = ROOT / ".local" / "telegram"
    local.mkdir(parents=True, exist_ok=True)
    store = Store(local / "requests.sqlite3")
    api = Telegram(token)
    try:
        me = await api.call("getMe")
        webhook = await api.call("getWebhookInfo")
        if webhook.get("url"):
            raise RuntimeError("An existing webhook is configured; polling was not started.")
        LOG.info("Customer bot @%s started", me["username"])
        offset = None
        while True:
            try:
                updates = await api.call(
                    "getUpdates",
                    offset=offset,
                    timeout=25,
                    allowed_updates=["message", "callback_query"],
                )
                for update in updates:
                    if update.get("callback_query"):
                        try:
                            await api.call(
                                "answerCallbackQuery",
                                callback_query_id=update["callback_query"]["id"],
                            )
                        except TelegramError:
                            LOG.info("Callback acknowledgment expired; processing the update")
                    result = await process(update, store, telegram=api)
                    if result:
                        result = await resolve(result, store)
                        try:
                            await api.deliver(result)
                        except TelegramError as error:
                            if error.status in (400, 403):
                                LOG.warning(
                                    "Telegram could not deliver a response (%s)", error.status
                                )
                                offset = update["update_id"] + 1
                                continue
                            raise
                        with store.db:
                            store.db.execute(
                                "INSERT INTO events(chat,direction,text) VALUES (?,?,?)",
                                (
                                    result["chat_id"],
                                    "bot",
                                    result["text"]
                                    + "\n"
                                    + "\n\n".join(
                                        f"{c['title']}\n{c['text']}"
                                        for c in result.get("cards", [])
                                    ),
                                ),
                            )
                    offset = update["update_id"] + 1
            except (httpx.HTTPError, RuntimeError) as error:
                # Never log HTTP exception text: request URLs contain the bot token.
                LOG.warning("Polling paused (%s); retrying in 5 seconds", type(error).__name__)
                await asyncio.sleep(5)
    finally:
        await api.client.aclose()
        store.db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        raise SystemExit(
            "Bot stopped: startup failed. Check configuration and connectivity."
        ) from None
