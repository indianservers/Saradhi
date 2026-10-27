"""Delegate coverage, quotes, stock reservation, acceptance and payments to the backend."""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from backend.integrations.telegram.backend_client import BackendError


def fingerprint(basket, profile):
    return hashlib.sha256(
        json.dumps(
            {
                "basket": basket,
                "method": profile.get("fulfillment"),
                "location": profile.get("location"),
                "address": profile.get("address"),
                "slots": profile.get("branch_slots"),
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()


async def execute(action, chat, store, backend, expected_quote=None):
    from backend.integrations.telegram.bot import reply

    profile = store.profile(chat)
    basket = profile.get("basket", [])
    catalog = store.catalog

    def output(text, buttons=("Cart", "Order status")):
        return {
            **reply(text),
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": b[0] if isinstance(b, tuple) else b,
                            "callback_data": b[1] if isinstance(b, tuple) else b,
                        }
                    ]
                    for b in buttons
                ]
            },
            "chat_id": chat,
        }

    if not backend.tokens:
        return output("Link your customer account first. No live order or payment was created.")
    if action == "quote":
        if not basket:
            return output("Cart is empty.")
        cart = await backend.call("POST", "/carts", {})
        address_cache = {}
        for line in basket:
            choice = next(
                ((r, d) for r, d in catalog.rows() if f"{r.id}/{d.id}" == line["selection"]), None
            )
            if not choice:
                raise BackendError("A dish is unavailable. Edit your cart before checkout.")
            restaurant, dish = choice
            if line["quantity"] > dish.available_quantity:
                raise BackendError("Requested quantity exceeds current stock.")
            slot = profile.get("branch_slots", {}).get(restaurant.branch_id)
            if not slot:
                raise BackendError("Choose a merchant-supported slot for every restaurant.")
            address_id = None
            if profile.get("fulfillment") != "pickup":
                gps = profile.get("location")
                if not gps:
                    raise BackendError("Share GPS to validate delivery coverage.")
                if restaurant.city_id not in address_cache:
                    address = await backend.call(
                        "POST",
                        "/addresses",
                        {
                            "city_id": restaurant.city_id,
                            "label": "Telegram delivery",
                            "address_text": profile.get("address", "Customer-shared GPS location"),
                            "latitude": str(round(gps["latitude"], 7)),
                            "longitude": str(round(gps["longitude"], 7)),
                        },
                    )
                    address_cache[restaurant.city_id] = address["id"]
                address_id = address_cache[restaurant.city_id]
            await backend.call(
                "POST",
                "/geo/serviceability",
                {
                    "branch_id": restaurant.branch_id,
                    "window_id": slot["id"],
                    "delivery_method": profile.get("fulfillment", "pickup"),
                    "address_id": address_id,
                    "category_id": dish.category_id,
                },
            )
            await backend.call(
                "POST",
                f"/carts/{cart['id']}/items",
                {
                    "branch_id": restaurant.branch_id,
                    "variant_id": dish.variant_id,
                    "quantity": line["quantity"],
                    "window_id": slot["id"],
                    "address_id": address_id,
                    "delivery_method": profile.get("fulfillment", "pickup"),
                    "option_ids": line["option_ids"],
                    "preparation_notes": line["notes"],
                },
            )
        quote = await backend.call("POST", f"/carts/{cart['id']}/quote", {})
        breakdown = quote.get("breakdown", {})
        if breakdown.get("delivery") is None:
            raise BackendError(
                "Delivery fee calculation is unavailable. No order was accepted. Try pickup."
            )
        profile["quote"] = {
            **quote,
            "fingerprint": fingerprint(basket, profile),
            "key": str(uuid.uuid4()),
        }
        with store.db:
            store.save_profile(chat, profile)
        lines = []
        for index, shipment in enumerate(quote.get("shipments", []), 1):
            start = datetime.fromisoformat(shipment["estimated_arrival_start"]).astimezone(
                ZoneInfo("Asia/Kolkata")
            )
            end = datetime.fromisoformat(shipment["estimated_arrival_end"]).astimezone(
                ZoneInfo("Asia/Kolkata")
            )
            lines.append(f"{index}. {shipment['branch_name']}")
            ids = set(shipment["line_ids"])
            for line in quote["lines"]:
                if str(line.get("cart_item_id")) in ids:
                    lines.append(
                        f"  {line['product_name']} · {line['variant_name']} x{line['quantity']}: "
                        f"{quote['currency']} {line['total']}"
                    )
            lines.append(
                f"  Items: {quote['currency']} {shipment['items']} | "
                f"Extras: {quote['currency']} {shipment['extras']}"
            )
            lines.append(f"  Delivery fee: {quote['currency']} {shipment['delivery_fee']}")
            label = (
                "Pickup window" if shipment["delivery_method"] == "pickup" else "Estimated arrival"
            )
            lines.append(
                f"  {label}: {start:%d %b, %I:%M %p} - {end:%d %b, %I:%M %p} IST (merchant slot)"
            )
            lines.append(f"  Restaurant total: {quote['currency']} {shipment['total']}")
        if not lines:
            lines = [
                f"{line['product_name']} x{line['quantity']}: {quote['currency']} {line['total']}"
                for line in quote["lines"]
            ]
        if len(quote.get("shipments", [])) > 1:
            lines.insert(
                0, "Separate deliveries: fees and arrival windows apply to each restaurant."
            )
        # The core rejects configured taxes without an approved calculator. Never invent rates.
        return output(
            "Combined checkout review\n"
            + "\n".join(lines)
            + "\n"
            + "\n".join(
                f"{name.title()}: {quote['currency']} {value}" for name, value in breakdown.items()
            )
            + "\n"
            "Extras are included in each line. Any later change requires a new quote.\n"
            f"Expires: {quote['expires_at']}\n"
            "Place order submits for merchant acceptance; it is not acceptance.",
            (("Place order", f"Confirm quote {quote['id']}"), "Cart"),
        )
    if action == "confirm":
        quote = profile.get("quote")
        if expected_quote is not None and (not quote or quote.get("id") != expected_quote):
            raise BackendError("That review is no longer current. Checkout again.")
        if not quote or quote["fingerprint"] != fingerprint(basket, profile):
            raise BackendError("Cart or location changed. Checkout again for a fresh quote.")
        if datetime.fromisoformat(quote["expires_at"]) <= datetime.now(UTC):
            raise BackendError("Quote expired. Checkout again.")
        if profile.get("last_quote") == quote["id"] and profile.get("order_id"):
            return output("This order was already submitted. Check Order status.")
        order = await backend.call(
            "POST", "/orders/confirm", {"quote_id": quote["id"]}, quote["key"]
        )
        profile.update(
            order_id=order["id"], last_basket=basket.copy(), last_quote=quote["id"], basket=[]
        )
        with store.db:
            store.save_profile(chat, profile)
        return output(
            f"Order request {order['id']} submitted. Awaiting merchant acceptance. "
            "No merchant acceptance or payment success is assumed.",
            ("Order status", "Restaurants"),
        )
    order_id = profile.get("order_id")
    if not order_id:
        return output("No live order yet.", ("Restaurants", "Cart"))
    order = await backend.call("GET", f"/orders/{order_id}")
    children = await backend.pages(f"/orders/{order_id}/merchant-orders")
    accepted = bool(children) and all(
        c["status"] in ("accepted", "preparing", "ready", "fulfilled") for c in children
    )
    if action == "status":
        return output(
            f"Order {order_id}\n"
            + "\n".join(f"Merchant {c['id']}: {c['status']}" for c in children)
            + (
                "\nAll merchants accepted." if accepted else "\nNot confirmed by all merchants yet."
            ),
            ("Pay live order", "Check live payment", "Restaurants")
            if accepted
            else ("Order status", "Restaurants"),
        )
    if action == "payment_status":
        payment = await backend.call("GET", f"/orders/{order_id}/payment")
        return output(
            f"Provider-verified backend payment status: {payment['status']}\n"
            "No screenshot or client-only success is trusted."
        )
    if action == "pay":
        if not accepted or order["status"] != "confirmed":
            raise BackendError(
                "Payment requires acceptance from every merchant and a payable order."
            )
        configuration = await backend.call("GET", "/payments/configuration")
        if not configuration.get("online_payment_available"):
            raise BackendError("The backend payment gateway is not configured.")
        intent = await backend.call(
            "POST", "/payments/intents", {"order_id": order_id}, f"telegram-{order_id}"
        )
        from backend.integrations.telegram.checkout_sessions import create

        url = create(chat, order_id, intent, configuration["mode"])
        result = output(
            f"Open the hosted checkout ({configuration['mode']}). "
            "Payment is confirmed only after backend signature/provider verification.",
            ("Check live payment", "Order status"),
        )
        result["checkout_url"] = url
        return result
    raise BackendError("Unsupported checkout action")
