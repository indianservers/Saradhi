"""Editable multi-item conversation state; live writes are delegated to backend actions."""

import json
import re
import uuid
from decimal import Decimal

from backend.integrations.telegram.catalog import card, load_catalog, matches
from backend.integrations.telegram.conversation import fuzzy_query, interpret, translate


class Shopping:
    def __init__(self, store):
        self.store = store
        self.catalog = getattr(store, "catalog", None) or load_catalog()

    def route(self, chat, text, state):
        profile = self.store.profile(chat)
        language = profile.get("language", "en")
        cart = profile.setdefault("basket", [])
        draft = state.get("shopping", {})

        def save():
            self.store.save_profile(chat, profile)

        def view(message, buttons=("Restaurants", "Cart", "Checkout", "Languages"), cards=None):
            navigation = [
                {
                    "text": translate(button[0] if isinstance(button, tuple) else button, language),
                    "callback_data": button[1] if isinstance(button, tuple) else button,
                }
                for button in buttons
            ]
            result = {
                "text": translate(message, language),
                "reply_markup": {
                    "inline_keyboard": [navigation[i : i + 2] for i in range(0, len(navigation), 2)]
                },
            }
            if cards:
                result["cards"] = cards
            return result

        def selected(selection):
            return next(
                ((r, d) for r, d in self.catalog.rows() if f"{r.id}/{d.id}" == selection), None
            )

        def item_card(restaurant, dish=None):
            result = card(restaurant, dish, self.catalog.demo)
            result["label"] = translate(result["label"], language)
            if dish:
                result["action"] = f"Pick {restaurant.id}/{dish.id}"
            return result

        if text == "Languages":
            return view("Choose language / భాష ఎంచుకోండి / भाषा चुनें", ("English", "తెలుగు", "हिन्दी"))
        if text in ("English", "తెలుగు", "हिन्दी"):
            profile["language"] = {"English": "en", "తెలుగు": "te", "हिन्दी": "hi"}[text]
            save()
            language = profile["language"]
            return view(translate("welcome", language))
        if text in ("/start", "/menu", "Main menu"):
            state.clear()
            state["screen"] = ""
            returning = (
                "\nOrder again uses your last request; location can be reused."
                if profile.get("last_basket")
                else "\n📍 Share GPS location before delivery checkout."
            )
            latest = self.store.db.execute(
                "SELECT data FROM requests WHERE chat=? ORDER BY id DESC LIMIT 1", (chat,)
            ).fetchone()
            if latest:
                returning += "\nLast request: " + json.loads(latest[0])["item"]
            return view(
                translate("welcome", language) + returning,
                (
                    "Food",
                    "Groceries",
                    "Essentials",
                    "All items",
                    "Restaurants",
                    "Stores",
                    "Cart",
                    "Favorites",
                    "Meal suggestions",
                    "Order status",
                    "Languages",
                    "Share GPS location",
                ),
            )
        if text == "Cancel" and draft:
            state.pop("shopping", None)
            return view("Selection cancelled. Your cart is retained.")
        if text in ("Food", "Groceries", "Essentials", "All items"):
            state.pop("step", None)
            state["screen"] = "browse"
            state["browse_kind"] = {
                "Food": "food",
                "Groceries": "groceries",
                "Essentials": "essentials",
            }.get(text)
            rows = [
                (r, d)
                for r, d in self.catalog.rows()
                if not state["browse_kind"] or d.kind == state["browse_kind"]
            ]
            return view(
                ("DEMO · " if self.catalog.demo else "LIVE · ")
                + (
                    f"{text}: compare prices and choose an item."
                    if rows
                    else f"No {text.lower()} are currently available."
                ),
                buttons=(
                    "Food",
                    "Groceries",
                    "Essentials",
                    "All items",
                    "Cart",
                    "Restaurants",
                    "Stores",
                ),
                cards=[item_card(r, d) for r, d in rows],
            )
        if text == "Stores":
            return view(
                "Choose a store.",
                cards=[item_card(r) for r in self.catalog.restaurants if r.kind != "food"],
            )
        if text == "Restaurants":
            state["screen"] = "browse"
            return view(
                ("DEMO · " if self.catalog.demo else "LIVE · ") + "Choose a restaurant.",
                cards=[item_card(r) for r in self.catalog.restaurants if r.kind == "food"],
            )
        if text.startswith("Menu "):
            restaurant = next((r for r in self.catalog.restaurants if r.id == text[5:]), None)
            state["viewing_restaurant"] = text[5:]
            return (
                view(
                    "Full menu",
                    buttons=("Save restaurant", "Cart", "Restaurants"),
                    cards=[item_card(restaurant, d) for d in restaurant.menu],
                )
                if restaurant
                else view("Restaurant is unavailable.")
            )
        if text.startswith("Pick "):
            choice = selected(text[5:])
            if not choice:
                return view("This item is no longer available.")
            restaurant, dish = choice
            state["shopping"] = {
                "selection": text[5:],
                "quantity": state.get("suggested_quantity", 1),
                "options": [],
                "notes": "",
            }
            return view(
                dish.name + "\n" + translate("choose", language),
                ("Qty 1", "Qty 2", "Qty 3", "Qty 4", "Qty 5", "Cancel"),
            )
        if text.startswith("Qty ") and draft:
            value = text[4:]
            if not value.isdigit() or not 1 <= int(value) <= 20:
                return view("Choose 1–20 portions.")
            draft["quantity"] = int(value)
            choice = selected(draft["selection"])
            if not choice:
                return view("Item no longer available.")
            restaurant, dish = choice
            if draft["quantity"] > dish.available_quantity:
                return view("Not enough stock for that quantity.")
            return view(
                "Choose customization. Portion sizes are merchant menu variants. "
                "Only offered options can change price.",
                ("Customize", "Preparation notes", "Add to cart", "Cancel"),
            )
        if draft and text.isdigit():
            return self.route(chat, "Qty " + text, state)
        candidate = (getattr(self.store, "neural", None) or {}).get("plan")
        if candidate and (draft or state.get("edit_line")) and not draft.get("await_notes"):
            from backend.integrations.telegram.dialogue_brain import Plan

            proposed = Plan.model_validate(candidate)
            if proposed.action == "cancel":
                return view(
                    "Cancel this selection? Your existing cart will be retained.",
                    ("Cancel", "Cart"),
                )
            current = (
                draft.get("quantity")
                if draft
                else next(
                    (line["quantity"] for line in cart if line["id"] == state.get("edit_line")),
                    None,
                )
            )
            if proposed.quantity and (
                proposed.quantity != current
                or re.search(r"portion|serving|people|quantity", text, re.I)
            ):
                button = ("Qty " if draft else "Set quantity ") + str(proposed.quantity)
                return view(
                    f"Use {proposed.quantity} portions? Confirm the change below.",
                    (button, "Cart", "Cancel"),
                )
            return view(
                "You are editing a selection. Choose the next change below.",
                ("Customize", "Preparation notes", "Add to cart", "Cancel")
                if draft
                else ("Cart", "Checkout"),
            )
        if text == "More options" and draft:
            count = len(draft.get("option_choices", []))
            draft["option_page"] = (draft.get("option_page", 0) + 1) % max(1, (count + 7) // 8)
            return self.route(chat, "Customize", state)
        if text in ("Customize", "Allergens") and draft:
            choice = selected(draft["selection"])
            if not choice:
                return view("Item unavailable.")
            _, dish = choice
            options = [(group, value) for group in dish.groups for value in group["values"]]
            draft["option_choices"] = options
            start = draft.get("option_page", 0) * 8
            visible = options[start : start + 8]
            if text == "Allergens":
                return view(
                    ", ".join(dish.allergens)
                    if dish.allergens_reviewed
                    else translate("missing", language),
                    ("Add to cart", "Customize", "Cancel"),
                )
            return view(
                "Select spice/extras supplied by this merchant. Tap again to remove.\n"
                + "\n".join(
                    f"{i + 1}. {g['name']} · {v['name']} · +₹{float(v['price_delta']):.2f}"
                    for i, (g, v) in enumerate(visible, start=start)
                )
                if options
                else "No customization options supplied by this merchant.",
                tuple(f"Option {i + 1}" for i in range(start, start + len(visible)))
                + (("More options",) if len(options) > 8 else ())
                + ("Preparation notes", "Add to cart", "Cancel"),
            )
        if text.startswith("Option ") and draft:
            try:
                index = int(text[7:]) - 1
                _, option = draft["option_choices"][index]
            except (ValueError, IndexError, KeyError):
                return view("Option no longer available.")
            option_id = str(option["id"])
            if option_id in draft["options"]:
                draft["options"].remove(option_id)
            else:
                draft["options"].append(option_id)
            return view(
                "Updated: " + option["name"], ("Customize", "Add to cart", "Preparation notes")
            )
        if text == "Preparation notes" and draft:
            draft["await_notes"] = True
            return view(
                "Type preparation notes (maximum 500 characters). "
                "Ingredient removal is a request, not an allergen safety guarantee.",
                ("Cancel",),
            )
        if draft.get("await_notes") and text:
            draft["notes"] = text[:500]
            draft.pop("await_notes", None)
            return view("Notes saved.", ("Add to cart", "Customize", "Cancel"))
        if text == "Add to cart" and draft:
            choice = selected(draft["selection"])
            if not choice:
                return view("Item no longer available.")
            restaurant, dish = choice
            options = [
                v for g in dish.groups for v in g["values"] if str(v["id"]) in draft["options"]
            ]
            for group in dish.groups:
                count = sum(str(v["id"]) in draft["options"] for v in group["values"])
                if not group["minimum"] <= count <= group["maximum"]:
                    return view(
                        f"Choose {group['minimum']}–{group['maximum']} for {group['name']}.",
                        ("Customize", "Cancel"),
                    )
            line = {
                "id": uuid.uuid4().hex[:10],
                "selection": draft["selection"],
                "item": dish.name,
                "restaurant": restaurant.name,
                "quantity": draft["quantity"],
                "price_minor": dish.price_minor,
                "option_ids": draft["options"],
                "options": options,
                "notes": draft["notes"],
            }
            if draft.get("editing"):
                cart[:] = [old for old in cart if old["id"] != draft["editing"]]
            if len(cart) >= 30:
                return view("Cart limit: 30 lines.", ("Cart",))
            cart.append(line)
            profile.pop("quote", None)
            save()
            state.pop("shopping", None)
            return view(translate("added", language))
        if text == "Cart":
            state["screen"] = "cart"
            if not cart:
                return view(translate("empty", language))
            lines = [
                f"{i + 1}. {line['item']} × {line['quantity']} · {line['restaurant']}\n"
                f"Notes: {line['notes'] or 'None'}"
                for i, line in enumerate(cart)
            ]
            return view(
                translate("cart", language) + "\n" + "\n".join(lines),
                tuple((f"Edit line {i + 1}", f"Edit {line['id']}") for i, line in enumerate(cart))
                + ("Checkout", "Restaurants", "Save favorite"),
            )
        if text.startswith(("Edit ", "Remove ")):
            action, line_id = text.split(" ", 1)
            line = next((line for line in cart if line["id"] == line_id), None)
            if not line:
                return view("Cart line not found.")
            if action == "Remove":
                cart.remove(line)
                profile.pop("quote", None)
                save()
                return view("Removed from cart.", ("Cart", "Restaurants"))
            state["edit_line"] = line_id
            return view(
                f"Edit {line['item']}",
                tuple(f"Set quantity {i}" for i in (1, 2, 3, 4, 5))
                + (f"Remove {line_id}", "Edit customization", "Cart"),
            )
        if text.startswith("Set quantity ") and state.get("edit_line"):
            value = text[13:]
            if value.isdigit() and 1 <= int(value) <= 20:
                line = next((line for line in cart if line["id"] == state["edit_line"]), None)
                if line:
                    line["quantity"] = int(value)
                    profile.pop("quote", None)
                    save()
            return view("Quantity updated.", ("Cart", "Checkout"))
        if text == "Edit customization" and state.get("edit_line"):
            line = next((line for line in cart if line["id"] == state["edit_line"]), None)
            if line:
                state["shopping"] = {
                    "editing": line["id"],
                    "selection": line["selection"],
                    "quantity": line["quantity"],
                    "options": line["option_ids"],
                    "notes": line["notes"],
                }
                return view(
                    "Change customization, then Add to cart.",
                    ("Customize", "Preparation notes", "Add to cart"),
                )
        if text == "Save favorite":
            favorites = profile.setdefault("favorites", [])
            for line in cart:
                if line["selection"] not in favorites:
                    favorites.append(line["selection"])
            save()
            return view("Cart dishes saved as favorites.", ("Favorites", "Cart"))
        if text == "Save restaurant" and state.get("viewing_restaurant"):
            restaurants = profile.setdefault("favorite_restaurants", [])
            if state["viewing_restaurant"] not in restaurants:
                restaurants.append(state["viewing_restaurant"])
            save()
            return view("Restaurant saved.", ("Favorites", "Restaurants"))
        if text == "Favorites":
            rows = [selected(s) for s in profile.get("favorites", [])]
            return view(
                "Favorites · unavailable dishes are hidden.",
                cards=[
                    item_card(r)
                    for r in self.catalog.restaurants
                    if r.id in profile.get("favorite_restaurants", [])
                ]
                + [item_card(*row) for row in rows if row],
            )
        if text == "Order again" and profile.get("last_basket"):
            available = [line for line in profile["last_basket"] if selected(line["selection"])]
            for line in available:
                restaurant, dish = selected(line["selection"])
                cart.append({**line, "id": uuid.uuid4().hex[:10], "price_minor": dish.price_minor})
            profile.pop("quote", None)
            save()
            return view(
                "Previous available dishes added at current prices. "
                "Review customization and stock again.",
                ("Cart", "Checkout"),
            )
        if text == "Checkout" and not cart:
            return view(translate("empty", language), ("Restaurants", "Cart"))
        if text in ("Checkout", "Pickup", "Delivery") and cart:
            state["screen"] = "checkout"
            if text == "Checkout":
                return view(
                    "Choose fulfillment. Delivery is checked by the backend "
                    "before accepting checkout.",
                    ("Pickup", "Delivery", "Cart"),
                )
            profile["fulfillment"] = "pickup" if text == "Pickup" else "courier"
            profile.pop("quote", None)
            profile["branch_slots"] = {}
            save()
            if text == "Delivery" and not profile.get("location"):
                return view(
                    "Share GPS location before delivery checkout.", ("Share GPS location", "Cart")
                )
            restaurant = selected(cart[0]["selection"])
            slots = restaurant[0].windows if restaurant else []
            if self.catalog.demo:
                groups = {}
                for line in cart:
                    choice = selected(line["selection"])
                    if not choice:
                        return view("An item is unavailable. Edit your cart.", ("Cart",))
                    merchant, dish = choice
                    group = groups.setdefault(
                        merchant.id, {"merchant": merchant, "items": [], "subtotal": 0}
                    )
                    total = (
                        line["price_minor"]
                        + sum(
                            int(Decimal(str(v["price_delta"])) * 100)
                            for v in line.get("options", [])
                        )
                    ) * line["quantity"]
                    group["subtotal"] += total
                    group["items"].append(
                        f"  {line['item']} x{line['quantity']}: INR {total / 100:.2f}"
                    )
                lines, grand = ["DEMO combined checkout - sample fees and arrival estimates"], 0
                for group in groups.values():
                    merchant = group["merchant"]
                    fee = merchant.demo_delivery_fee_minor if text == "Delivery" else 0
                    total = group["subtotal"] + fee
                    grand += total
                    lines.extend(
                        [
                            merchant.name,
                            *group["items"],
                            f"  Items and extras: INR {group['subtotal'] / 100:.2f}",
                            f"  Delivery fee: INR {fee / 100:.2f}",
                            (
                                f"  Estimated arrival: {merchant.demo_eta_minutes[0]}-"
                                f"{merchant.demo_eta_minutes[1]} min (sample)"
                                if text == "Delivery"
                                else "  Pickup: choose a live merchant slot"
                            ),
                            f"  Restaurant total: INR {total / 100:.2f}",
                        ]
                    )
                lines.extend(
                    [
                        f"Combined total: INR {grand / 100:.2f}",
                        "DEMO only: no order accepted or payment taken. "
                        "Live taxes, discounts, coverage and scheduling require a server quote.",
                    ]
                )
                return view("\n".join(lines), ("Cart", "Restaurants", "Food"))
            state["slot_choices"] = slots
            return view(
                "Choose a slot for "
                + restaurant[0].name
                + " (starts/ends UTC):\n"
                + "\n".join(
                    f"{i + 1}. {s['starts_at']} → {s['ends_at']}" for i, s in enumerate(slots)
                ),
                tuple(f"Slot {i + 1}" for i in range(len(slots))) + ("Cart",),
            )
        if text.startswith("Slot ") and cart:
            try:
                slot = state["slot_choices"][int(text[5:]) - 1]
            except (KeyError, IndexError, ValueError):
                return view("Slot expired. Start Checkout again.")
            profile["selected_slot"] = slot
            profile.setdefault("branch_slots", {})[slot["branch_id"]] = slot
            save()
            remaining = [selected(line["selection"]) for line in cart]
            remaining = [
                row[0]
                for row in remaining
                if row and row[0].branch_id not in profile["branch_slots"]
            ]
            if remaining:
                restaurant = remaining[0]
                state["slot_choices"] = restaurant.windows
                return view(
                    "Choose a slot for "
                    + restaurant.name
                    + "\n"
                    + "\n".join(
                        f"{i + 1}. {s['starts_at']} → {s['ends_at']}"
                        for i, s in enumerate(restaurant.windows)
                    ),
                    tuple(f"Slot {i + 1}" for i in range(len(restaurant.windows))) + ("Cart",),
                )
            result = view("Checking live availability, coverage and price breakdown…")
            result["live_action"] = "quote"
            return result
        if text.startswith("Confirm quote "):
            if draft:
                return view(
                    "Finish your current selection or cancel before confirming.", ("Cart", "Cancel")
                )
            result = view("Submitting the reviewed quote…")
            result["live_action"] = "confirm"
            result["expected_quote"] = text[14:]
            return result
        if text == "Place order":
            return view("Open checkout and confirm the current quote.", ("Checkout", "Cart"))
        if text in ("Order status", "Pay live order", "Check live payment"):
            result = view("Checking live order…")
            result["live_action"] = {
                "Order status": "status",
                "Pay live order": "pay",
                "Check live payment": "payment_status",
            }[text]
            return result
        if text.startswith("Meal suggestions"):
            state["suggesting"] = True
            return view(
                "Tell me a total budget and number of people, e.g. ‘under 600 for 2 people’. "
                "Suggestions are menu prices before confirmed fees.",
                ("Restaurants", "Cart"),
            )
        if text.startswith("Combo "):
            try:
                combo = state["meal_combos"][int(text[6:]) - 1]
            except (ValueError, KeyError, IndexError):
                return view("Suggestion expired. Ask for a new meal suggestion.")
            choices = [selected(selection) for selection in combo["selections"]]
            if not all(choices) or len(cart) + len(choices) > 30:
                return view("Meal unavailable or cart limit reached.")
            if any(group["minimum"] for r, d in choices for group in d.groups):
                return view("This meal needs customization. Select dishes individually.")
            for restaurant, dish in choices:
                cart.append(
                    {
                        "id": uuid.uuid4().hex[:10],
                        "selection": f"{restaurant.id}/{dish.id}",
                        "item": dish.name,
                        "restaurant": restaurant.name,
                        "quantity": combo["people"],
                        "price_minor": dish.price_minor,
                        "option_ids": [],
                        "options": [],
                        "notes": "",
                    }
                )
            profile.pop("quote", None)
            save()
            return view("Meal added. Review before checkout.", ("Cart", "Checkout"))
        parsed = interpret(text, getattr(self.store, "neural", None))
        neural = getattr(self.store, "neural", None) or {}
        if neural.get("plan") and not draft:
            from backend.integrations.telegram.dialogue_brain import Plan, route_plan, search_query

            plan = Plan.model_validate(neural["plan"])
            # Model-selected tool arguments replace keyword queries, not commerce validation.
            if plan.action == "clarify":
                messages = {
                    "ask_dish": "Which item, restaurant or store do you mean?",
                    "ask_item": "Which item should I show first? "
                    "You can add several products to your cart.",
                    "ask_pack": "Which pack size do you want? Select a product, "
                    "then choose the number of packs. "
                    "I will not assume kg or litres mean pack counts.",
                    "ask_allergens": "Select a dish to see merchant allergen information. "
                    "Missing data is not an allergy safety guarantee.",
                    "review_required": "Review your cart before confirming. "
                    "I cannot submit or pay without your confirmation.",
                    "unsupported": "I can use published menu facts, "
                    "but cannot invent prices or availability.",
                }
                if plan.step == "ask_pack":
                    state.pop("suggested_quantity", None)
                    return view(
                        messages["ask_pack"],
                        cards=[item_card(r, d) for r, d in matches(self.catalog, plan.dish)]
                        if plan.dish
                        else None,
                    )
                return view(messages.get(plan.step, "Please tell me which item you want."))
            if plan.action == "explain":
                messages = {
                    "explain_location": "GPS is used to check merchant delivery coverage. "
                    "You can use pickup without sharing GPS.",
                    "explain_payment": "Payments require merchant acceptance "
                    "and provider verification. "
                    "A screenshot is not proof of payment.",
                }
                return view(
                    messages.get(plan.step, "Choose an option and I will help you review it.")
                )
            if plan.action == "search":
                state["screen"] = "search"
                direct_query = fuzzy_query(text.lower(), self.catalog)
                dish_words = {
                    word
                    for _, dish in self.catalog.rows()
                    for word in re.findall(r"[a-z]+", dish.name.lower())
                }
                explicit_dish = " ".join(
                    word for word in re.findall(r"[a-z]+", text.lower()) if word in dish_words
                )
                if (
                    explicit_dish
                    and matches(self.catalog, direct_query)
                    and not matches(self.catalog, plan.dish)
                ):
                    # Ground unknown/new dish names in this merchant catalog, not training labels.
                    plan.dish = explicit_dish[:100]
                state["brain_memory"] = {
                    key: value
                    for key, value in plan.model_dump().items()
                    if key in ("dish", "quantity", "budget", "diet", "sort", "stage")
                }
                state["brain_memory"]["stage"] = "search"
                parsed = {
                    "intent": "search",
                    "query": search_query(plan),
                    "quantity": plan.quantity,
                    "budget": plan.budget,
                    "action": None,
                }
            else:
                route = route_plan(plan)
                if route and route != text:
                    return self.route(chat, route, state)
                if plan.action in ("repeat", "cancel", "pickup", "delivery"):
                    button = {
                        "repeat": "Order again",
                        "cancel": "Cancel",
                        "pickup": "Pickup",
                        "delivery": "Delivery",
                    }[plan.action]
                    return view(
                        "Please confirm this change using the button below.", (button, "Cart")
                    )
                if plan.action == "allergens":
                    return view(
                        "Select a dish to review its merchant-provided ingredients "
                        "and allergen information.",
                        ("Restaurants", "Cart"),
                    )
        if parsed.get("action") and parsed["action"] != text and not draft:
            return self.route(chat, parsed["action"], state)
        if parsed["intent"] in ("cheaper", "vegetarian", "vegan"):
            query = (
                state.get("search_query", "")
                + " "
                + {"cheaper": "cheapest", "vegetarian": "vegetarian", "vegan": "vegan"}[
                    parsed["intent"]
                ]
            )
        else:
            query = parsed.get("query", text)
        if text in ("Biryani",) or (
            not draft
            and not state.get("step")
            and not text.startswith(("/", "Pay request", "Check payment", "Page ", "Select "))
            and text
            not in (
                "Payment",
                "Help",
                "My requests",
                "Share GPS location",
                "Forget location",
                "Use saved location",
                "Cancel",
                "Submit request",
            )
        ):
            if not query:
                return None
            if (
                not neural.get("plan")
                and re.search(r"\b(cheaper|under|below|for|vegetarian|vegan)\b", query)
                and state.get("search_query")
                and not any(d.name.lower() in query for _, d in self.catalog.rows())
            ):
                query = re.sub(r"(?:under|below)\s*\d+", "", state["search_query"]) + " " + query
            query = fuzzy_query(query, self.catalog)
            dietary = next(
                (
                    d
                    for d in ("vegan", "gluten_free", "jain", "halal")
                    if d.replace("_", " ") in query or d in query
                ),
                None,
            )
            search_query = (
                query.replace(dietary.replace("_", " "), "").replace(dietary, "").strip()
                if dietary
                else query
            )
            rows = matches(self.catalog, search_query) if search_query else self.catalog.rows()
            if dietary:
                rows = [(r, d) for r, d in rows if dietary in d.dietary]
            quantity, budget = parsed.get("quantity"), parsed.get("budget")
            if quantity and budget:
                rows = [
                    (r, d)
                    for r, d in rows
                    if d.kind == "food" or d.price_minor * quantity <= budget * 100
                ]

            if state.get("suggesting"):
                from itertools import combinations

                people = parsed.get("quantity") or 1
                budget = parsed.get("budget")
                rows = sorted(self.catalog.rows(), key=lambda row: row[1].price_minor)
                if budget:
                    rows = [(r, d) for r, d in rows if d.price_minor * people <= budget * 100]
                combos = []
                if budget:
                    for (r, a), (other, b) in combinations(rows, 2):
                        total = (a.price_minor + b.price_minor) * people
                        if (
                            r.id == other.id
                            and total <= budget * 100
                            and min(a.available_quantity, b.available_quantity) >= people
                        ):
                            combos.append(
                                {
                                    "selections": [f"{r.id}/{a.id}", f"{r.id}/{b.id}"],
                                    "people": people,
                                    "text": f"{a.name} + {b.name} · {r.name} · "
                                    f"{people} each · ₹{total / 100:.2f}",
                                }
                            )
                        if len(combos) >= 3:
                            break
                state["meal_combos"] = combos
                rows = rows[:3]
                state.pop("suggesting", None)
                return view(
                    f"Meal options for {people} people. Item prices only; "
                    "fees are checked at checkout.\n"
                    + "\n".join(f"{i + 1}. {combo['text']}" for i, combo in enumerate(combos)),
                    buttons=tuple(f"Combo {i + 1}" for i in range(len(combos)))
                    + ("Cart", "Restaurants"),
                    cards=[item_card(r, d) for r, d in rows],
                )
            if rows:
                state["screen"] = "search"
                state["search_query"] = query[:500]
                if parsed.get("quantity"):
                    state["suggested_quantity"] = parsed["quantity"]
                if not neural.get("plan"):
                    from backend.integrations.telegram.commerce_nlp_data import PRODUCTS
                    from backend.integrations.telegram.nlp_dataset import DISHES

                    names = sorted([*DISHES, *PRODUCTS], key=len, reverse=True)
                    dish = next(
                        (
                            d
                            for d in names
                            if re.search(r"(?<!\w)" + re.escape(d) + r"(?!\w)", query.lower())
                        ),
                        rows[0][1].name.lower().split(" · ")[0],
                    )
                    old_memory = state.get("brain_memory", {})
                    budget_match = re.search(r"(?:under|below)\s*(\d+)", query)
                    remembered_budget = (
                        int(budget_match[1]) if budget_match else old_memory.get("budget")
                    )
                    state["brain_memory"] = {
                        "dish": dish,
                        "quantity": parsed.get("quantity") or old_memory.get("quantity"),
                        "budget": remembered_budget
                        if remembered_budget and remembered_budget <= 1000000
                        else None,
                        "diet": "vegetarian" if "vegetarian" in query else "",
                        "sort": "price" if "cheapest" in query else "",
                        "stage": "search",
                    }
                return view(
                    ("DEMO · " if self.catalog.demo else "LIVE · ")
                    + "Matching products. Select a pack/item to customize and add to cart.",
                    cards=[item_card(r, d) for r, d in rows],
                )
            if neural.get("plan"):
                return view(
                    "No available menu items match those requirements. "
                    "Change a filter or browse restaurants.",
                    ("Restaurants", "Cart"),
                )
        return None
