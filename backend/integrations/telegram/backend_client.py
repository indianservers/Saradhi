"""Customer-authenticated HTTP bridge; no bot-wide customer or administrator token."""

import os
from datetime import UTC, datetime
from decimal import Decimal

import httpx

from backend.integrations.telegram.catalog import Catalog, Dish, Restaurant

API = os.environ.get("QUICKBUDDY_API_URL", "http://127.0.0.1:8001/api/v1").rstrip("/")


class BackendError(Exception):
    pass


class Backend:
    def __init__(self, chat, vault, transport=None):
        self.chat, self.vault = chat, vault
        self.tokens = vault.get(chat)
        self.client = httpx.AsyncClient(base_url=API, timeout=15, transport=transport)

    async def call(self, method, path, body=None, key=None):
        if not self.tokens:
            raise BackendError("Link your customer account on the control page first.")
        headers = {"Authorization": "Bearer " + self.tokens["access_token"]}
        if key:
            headers["Idempotency-Key"] = key
        response = await self.client.request(method, path, json=body, headers=headers)
        if response.status_code == 401 and self.tokens.get("refresh_token"):
            refresh = await self.client.post(
                "/auth/refresh", json={"refresh_token": self.tokens["refresh_token"]}
            )
            if refresh.is_success:
                self.tokens = refresh.json()
                self.vault.save(self.chat, self.tokens)
                headers["Authorization"] = "Bearer " + self.tokens["access_token"]
                response = await self.client.request(method, path, json=body, headers=headers)
        if not response.is_success:
            try:
                error = response.json().get("error", {})
                message = error.get("message", "") if isinstance(error, dict) else ""
            except ValueError:
                message = ""
            raise BackendError(message or f"Backend request unavailable ({response.status_code}).")
        return response.json() if response.content else None

    async def pages(self, path):
        result, cursor = [], None
        for _ in range(50):
            separator = "&" if "?" in path else "?"
            page = await self.call(
                "GET", path + separator + "limit=100" + ("&cursor=" + cursor if cursor else "")
            )
            result.extend(page["items"])
            cursor = page.get("next_cursor")
            if not cursor:
                return result
        raise BackendError("Catalog page limit reached; narrow the selected city.")

    async def catalog(self, city_id=None):
        suffix = "?city_id=" + city_id if city_id else ""
        rows = await self.pages("/channel/catalog" + suffix)
        branches = await self.pages("/merchants/branches" + suffix)
        branch_map = {b["id"]: b for b in branches}
        grouped = {}
        for row in rows:
            if row.get("merchant_type") == "pharmacy" or row.get("category_name", "").lower() in (
                "medicines",
                "medicine",
                "pharmacy",
                "pharmaceuticals",
            ):
                continue
            kind = {"grocery": "groceries", "retail": "essentials"}.get(
                row.get("merchant_type"), "food"
            )
            branch = branch_map.get(row["branch_id"])
            if not branch or row["currency"] != "INR":
                continue
            bid = row["branch_id"]
            if bid not in grouped:
                windows = await self.pages(f"/merchants/branches/{bid}/windows")
                windows = [
                    w
                    for w in windows
                    if w["reserved"] < w["capacity"]
                    and datetime.fromisoformat(w["starts_at"]) > datetime.now(UTC)
                ]
                if not windows:
                    continue
                grouped[bid] = Restaurant(
                    id=bid.replace("-", "")[:12],
                    name=row["branch_name"],
                    kind=kind,
                    city=branch.get("city_id", "Unknown"),
                    branch_id=bid,
                    city_id=branch.get("city_id"),
                    windows=windows,
                    menu=[],
                )
            dietary = row.get("dietary", [])
            grouped[bid].menu.append(
                Dish(
                    id=row["variant_id"].replace("-", "")[:12],
                    variant_id=row["variant_id"],
                    category_id=row["category_id"],
                    kind=kind,
                    unit=row.get("unit") or ("portion" if kind == "food" else "item"),
                    name=(row["name"] + " · " + row["variant_name"])[:100],
                    price_minor=int(Decimal(row["unit_price"]) * 100),
                    vegetarian="vegetarian" in dietary or "vegan" in dietary,
                    dietary=dietary,
                    image_url=row.get("image_url"),
                    ingredients=row.get("ingredients"),
                    allergens=row.get("allergens", []),
                    allergens_reviewed=row.get("allergens_reviewed", False),
                    groups=row.get("groups", []),
                    available_quantity=float(row["available_quantity"]),
                    rating=row.get("average_rating"),
                    rating_count=row.get("review_count", 0),
                )
            )
        return Catalog(demo=False, restaurants=list(grouped.values()))
