"""Typed dialogue plans, conversation memory and a bounded tool interface."""

import difflib
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from backend.integrations.telegram.brain_data import prompt

Action = Literal[
    "groceries",
    "essentials",
    "stores",
    "browse_all",
    "search",
    "clarify",
    "explain",
    "restaurants",
    "cart",
    "checkout",
    "confirm",
    "cancel",
    "cheaper",
    "vegetarian",
    "vegan",
    "favorites",
    "repeat",
    "location",
    "pickup",
    "delivery",
    "orders",
    "allergens",
    "suggest",
    "help",
    "quantity",
]


class Memory(BaseModel):
    dish: str = Field(default="", max_length=100)
    quantity: int | None = Field(default=None, ge=1, le=20)
    budget: int | None = Field(default=None, ge=1, le=1000000)
    diet: Literal["", "vegetarian", "vegan", "gluten_free", "jain", "halal"] = ""
    sort: Literal["", "price", "rating"] = ""
    stage: str = Field(default="", max_length=30)


class Plan(Memory):
    action: Action
    step: Literal[
        "show_matches",
        "open_screen",
        "ask_dish",
        "ask_pack",
        "ask_item",
        "ask_allergens",
        "explain_location",
        "explain_payment",
        "unsupported",
        "review_required",
    ]
    confidence: float = Field(ge=0, le=1)
    source: str = "tensorflow_context_decoder"


def context_for(state, profile, catalog=None):
    from backend.integrations.telegram.commerce_nlp_data import canonical_item_name

    try:
        memory = Memory.model_validate(state.get("brain_memory", {}))
    except ValidationError:
        memory = Memory()
    if state.get("shopping"):
        memory.stage = "customize"
        draft = state["shopping"]
        memory.quantity = draft.get("quantity") or memory.quantity
        if catalog:
            choice = next(
                (d for r, d in catalog.rows() if f"{r.id}/{d.id}" == draft["selection"]), None
            )
            if choice:
                memory.dish = canonical_item_name(choice.name)
    elif state.get("edit_line"):
        line = next(
            (line for line in profile.get("basket", []) if line["id"] == state["edit_line"]), None
        )
        if line:
            memory.dish = canonical_item_name(line["item"])
            memory.quantity = line["quantity"]
            memory.stage = "cart"
    elif state.get("screen"):
        memory.stage = state["screen"]
    elif profile.get("basket") and memory.stage != "search":
        memory.stage = "cart"
    return memory


def parse_plan(raw, confidence, context):
    parts = [part.strip() for part in raw.strip().split("|")]
    if len(parts) != 7:
        return None
    action, dish, quantity, budget, diet, sort, step = parts
    from backend.integrations.telegram.commerce_nlp_data import normalize_product_names

    dish = normalize_product_names(dish)
    try:
        plan = Plan(
            action=action,
            dish=dish,
            quantity=int(quantity) if quantity else None,
            budget=int(budget) if budget else None,
            diet=diet,
            sort=sort,
            step=step,
            confidence=confidence,
        )
    except (ValidationError, ValueError):
        return None
    # Old action-only examples can still resolve against current memory.
    if action in ("cheaper", "vegetarian", "vegan", "quantity"):
        plan.action = "search" if context.dish else "clarify"
        plan.step = "show_matches" if context.dish else "ask_dish"
        plan.dish = plan.dish or context.dish
        plan.quantity = plan.quantity or context.quantity
        plan.budget = plan.budget or context.budget
        plan.diet = (action if action in ("vegetarian", "vegan") else plan.diet) or context.diet
        plan.sort = "price" if action == "cheaper" else plan.sort or context.sort
    return plan


def grounded_plan(plan, text, memory):
    """Reject unexplained numeric changes. Never provides price/payment authority."""
    if plan is None or plan.confidence < 0.85:
        return None
    normalized = text.lower()
    for word, value in (
        ("one", "1"),
        ("two", "2"),
        ("three", "3"),
        ("four", "4"),
        ("five", "5"),
        ("six", "6"),
        ("seven", "7"),
        ("eight", "8"),
        ("nine", "9"),
        ("ten", "10"),
        ("రెండు", "2"),
        ("दो", "2"),
    ):
        normalized = re.sub(r"(?<!\w)" + word + r"(?!\w)", value, normalized)
    if plan.action == "search" and plan.dish and plan.dish != memory.dish:
        # A model may not invent a requested dish. Allow literal names, localized
        # names and close spelling matches, while requiring evidence in the message.
        from backend.integrations.telegram.commerce_nlp_data import PRODUCT_ALIASES
        from backend.integrations.telegram.nlp_dataset import DISHES

        aliases = (plan.dish, *DISHES.get(plan.dish, ()), *PRODUCT_ALIASES.get(plan.dish, ()))
        words = re.findall(r"\w+", normalized)
        width = len(plan.dish.split())
        windows = [" ".join(words[i : i + width]) for i in range(len(words))]
        supported = any(name in normalized for name in aliases) or any(
            difflib.SequenceMatcher(None, plan.dish, phrase).ratio() >= 0.82 for phrase in windows
        )
        if not supported:
            return Plan(action="clarify", step="ask_dish", confidence=plan.confidence)
    if plan.action == "search" and re.search(
        r"\d+\s*(?:kg|kilograms?|litres?|liters?|ml|grams?|g)\b", normalized
    ):
        packs = re.search(r"(\d+)\s*(?:packs?|packets?|bags?|bottles?)\b", normalized)
        if not packs or plan.quantity != int(packs[1]):
            return Plan(
                action="clarify", dish=plan.dish, step="ask_pack", confidence=plan.confidence
            )
    numbers = set(re.findall(r"\d+", normalized))
    for key in ("quantity", "budget"):
        value = getattr(plan, key)
        old = getattr(memory, key)
        permitted = set(numbers)
        if key == "quantity" and memory.quantity:
            if re.search(r"\b(double|doubling|twice)\b", normalized):
                permitted.add(str(memory.quantity * 2))
            if re.search(r"\b(half|halve|halving)\b", normalized) and memory.quantity % 2 == 0:
                permitted.add(str(memory.quantity // 2))
        if value is not None and value != old and str(value) not in permitted:
            return None
    if plan.action == "search" and not plan.dish:
        plan.action, plan.step = "clarify", "ask_dish"
    if (
        memory.dish
        and plan.action == "search"
        and plan.dish != memory.dish
        and re.search(r"\b(same|that|those|these|cheaper)\b", normalized)
        and plan.dish not in normalized
    ):
        return None
    return plan


def model_input(text, memory):
    return prompt(text, memory.model_dump(exclude_none=True))


def search_query(plan):
    dish = plan.dish
    if plan.diet in ("vegetarian", "vegan"):
        dish = re.sub(r"\b(chicken|mutton|egg)\b", "", dish).strip()
    if plan.diet == "vegan":
        dish = re.sub(r"\bpaneer\b", "", dish).strip()
    values = [dish]
    if plan.diet:
        values.append(plan.diet.replace("_", " "))
    if plan.budget:
        values.append(f"under {plan.budget}")
    if plan.sort == "price":
        values.append("cheapest")
    return " ".join(values)


def route_plan(plan):
    """Only discovery/screens can be automatic. Every write retains explicit UI confirmation."""
    return {
        "groceries": "Groceries",
        "essentials": "Essentials",
        "stores": "Stores",
        "browse_all": "All items",
        "restaurants": "Restaurants",
        "cart": "Cart",
        "favorites": "Favorites",
        "orders": "Order status",
        "help": "Help",
        "suggest": "Meal suggestions",
        "checkout": "Checkout",
        "confirm": "Checkout",
        "location": "Share GPS location",
    }.get(plan.action)
