"""Validated channel catalog. Demo records never qualify for payment."""

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator

ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = ROOT / ".local/telegram/catalog.json"


class Dish(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]{1,24}$")
    name: str = Field(min_length=1, max_length=100)
    price_minor: int = Field(gt=0, le=10000000)
    kind: Literal["food", "groceries", "essentials", "medicines"] = "food"
    unit: str = "portion"
    vegetarian: bool = False
    image_url: HttpUrl | None = None
    dietary: list[str] = Field(default_factory=list)
    ingredients: list[str] | None = None
    allergens: list[str] = Field(default_factory=list)
    allergens_reviewed: bool = False
    groups: list[dict] = Field(default_factory=list)
    variant_id: str | None = None
    category_id: str | None = None
    available_quantity: float = 999
    rating: float | None = Field(default=None, ge=0, le=5)
    rating_count: int = Field(default=0, ge=0)


class Restaurant(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]{1,24}$")
    name: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=80)
    kind: Literal["food", "groceries", "essentials", "medicines"] = "food"
    rating: float | None = Field(default=None, ge=0, le=5)
    rating_count: int = Field(default=0, ge=0)
    rating_source: str = "Not rated"
    image_url: HttpUrl | None = None
    menu: list[Dish] = Field(max_length=200)
    branch_id: str | None = None
    city_id: str | None = None
    windows: list[dict] = Field(default_factory=list)
    demo_delivery_fee_minor: int = Field(default=0, ge=0)
    demo_eta_minutes: tuple[int, int] = (25, 45)


class Catalog(BaseModel):
    demo: bool = True
    restaurants: list[Restaurant] = Field(max_length=50)

    @model_validator(mode="after")
    def remove_medicines(self):
        self.restaurants = [r for r in self.restaurants if r.kind != "medicines"]
        for restaurant in self.restaurants:
            restaurant.menu = [d for d in restaurant.menu if d.kind != "medicines"]
        self.restaurants = [r for r in self.restaurants if r.menu]
        return self

    def rows(self):
        return [(r, d) for r in self.restaurants for d in r.menu]


def load_catalog():
    path = CATALOG_PATH if CATALOG_PATH.exists() else Path(__file__).with_name("demo-catalog.json")
    return Catalog.model_validate_json(path.read_text(encoding="utf-8"))


def save_catalog(value):
    catalog = Catalog.model_validate(value)
    ids = [r.id for r in catalog.restaurants]
    if len(set(ids)) != len(ids):
        raise ValueError("Restaurant IDs must be unique")
    for restaurant in catalog.restaurants:
        items = [d.id for d in restaurant.menu]
        if len(set(items)) != len(items):
            raise ValueError("Dish IDs must be unique within each restaurant")
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = CATALOG_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(catalog.model_dump(mode="json"), indent=2), encoding="utf-8")
    temp.replace(CATALOG_PATH)
    return catalog


def matches(catalog, query):
    terms = set(re.findall(r"[a-z]+", query.lower()))
    nonveg = bool(re.search(r"\bnon[- ]?(?:veg|vegetarian)\b", query.lower()))
    veg = not nonveg and (
        bool(terms & {"vegetarian", "veg"})
        or bool(re.search(r"without meat|no meat|meat[- ]free", query.lower()))
    )
    excluded = set(re.findall(r"(?:without|no)\s+(chicken|mutton|egg|paneer)", query.lower()))
    budget = re.search(
        r"(?:under|below|less than|budget|within|at most|ceiling of|₹|rs\.?)[ ]*(\d+)",
        query.lower(),
    )
    ceiling = int(budget[1]) * 100 if budget else None
    stop = {
        "i",
        "want",
        "a",
        "an",
        "the",
        "some",
        "please",
        "show",
        "me",
        "find",
        "for",
        "under",
        "below",
        "less",
        "than",
        "budget",
        "best",
        "rated",
        "near",
        "nearby",
        "my",
        "location",
        "restaurants",
        "restaurant",
        "from",
        "rs",
        "food",
        "order",
        "get",
        "can",
        "you",
        "would",
        "like",
        "to",
        "eat",
        "hungry",
        "something",
    }
    search = terms - stop - excluded - {"without", "no"}
    if veg:
        search -= {"meat", "free"}
    if nonveg:
        search -= {"non", "veg", "nonveg", "nonvegetarian"}
    vocabulary = set()
    for restaurant, dish in catalog.rows():
        vocabulary.update(re.findall(r"[a-z]+", f"{restaurant.name} {dish.name}".lower()))
    required = search & vocabulary
    rows = []
    for restaurant, dish in catalog.rows():
        words = set(re.findall(r"[a-z]+", f"{restaurant.name} {dish.name}".lower()))
        score = len(search & words)
        if veg and not dish.vegetarian:
            continue
        if nonveg and dish.vegetarian:
            continue
        if excluded & words:
            continue
        if ceiling is not None and dish.price_minor > ceiling:
            continue
        if required and not required.issubset(words):
            continue
        if search and not score and not (veg and search <= {"vegetarian", "veg"}):
            continue
        rows.append((score, restaurant, dish))
    if terms & {"cheaper", "cheapest", "affordable"}:
        rows.sort(key=lambda row: (row[2].price_minor, -(row[1].rating or 0)))
    else:
        rows.sort(key=lambda row: (-row[0], -(row[1].rating or 0), row[2].price_minor))
    return [(r, d) for _, r, d in rows]


def card(restaurant, dish=None, demo=True):
    rating = (
        f"★ {restaurant.rating:.1f}/5 · {restaurant.rating_count} ratings · "
        f"{restaurant.rating_source}"
        if restaurant.rating is not None
        else "No ratings yet"
    )
    name = dish.name if dish else restaurant.name
    if dish and dish.rating is not None:
        rating = f"Dish ★ {dish.rating:.1f}/5 · {dish.rating_count} published reviews"
    kind = dish.kind if dish else restaurant.kind
    merchant_label = "Restaurant" if kind == "food" else "Store"
    detail = f"{merchant_label}: {restaurant.name} · {restaurant.city}\n{rating}"
    if dish:
        detail += f"\n₹{dish.price_minor / 100:.2f} · " + (
            f"per {dish.unit}"
            if kind != "food"
            else "Vegetarian"
            if dish.vegetarian
            else "Non-veg"
            if demo or "non_vegetarian" in dish.dietary
            else "Dietary labels not supplied"
        )
    return {
        "title": name,
        "kind": kind,
        "merchant": restaurant.name,
        "price_minor": dish.price_minor if dish else None,
        "unit": dish.unit if dish else None,
        "text": detail
        + (
            "\nIngredients: "
            + (
                ", ".join(dish.ingredients)[:250]
                if dish.ingredients is not None
                else "Not supplied"
            )
            + "\nAllergens: "
            + (
                (", ".join(dish.allergens) or "None declared")
                if dish.allergens_reviewed
                else "Missing information — ask merchant"
            )
            if dish
            else ""
        ),
        "demo": demo,
        "image_url": str(dish.image_url or restaurant.image_url)
        if (dish and dish.image_url) or restaurant.image_url
        else None,
        "action": f"Select {restaurant.id}/{dish.id}" if dish else f"Menu {restaurant.id}",
        "label": "Choose item" if dish else "View full menu",
    }
