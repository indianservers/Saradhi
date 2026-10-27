"""Razorpay TEST payment links. No live charges or fulfillment from this pilot."""

import json
import os

import httpx
from dotenv import dotenv_values

from backend.integrations.telegram.bot import ROOT, reply


def credentials():
    values = dotenv_values(ROOT / ".secrets/razorpay-test.env")
    key = os.environ.get("TELEGRAM_RAZORPAY_TEST_KEY_ID") or values.get("RAZORPAY_KEY_ID", "")
    secret = os.environ.get("TELEGRAM_RAZORPAY_TEST_KEY_SECRET") or values.get(
        "RAZORPAY_KEY_SECRET", ""
    )
    return (key, secret) if key.startswith("rzp_test_") and secret else None


async def resolve(result, store, transport=None):
    action = result.pop("payment_action", None)
    if not action:
        return result
    chat = result["chat_id"]
    row = store.db.execute(
        "SELECT data FROM requests WHERE id=? AND chat=?", (action["request"], chat)
    ).fetchone()
    if not row:
        return {**reply("Request not found."), "chat_id": chat}
    order = json.loads(row[0])
    auth = credentials()
    if not auth:
        return {
            **reply(
                "Razorpay TEST credentials are not configured yet. "
                "No payment link created or money collected."
            ),
            "chat_id": chat,
        }
    amount = order.get("price_minor", 0) * order["quantity"]
    if not amount:
        return {
            **reply(
                "This request has no priced restaurant selection. "
                "Choose an item from a restaurant card first."
            ),
            "chat_id": chat,
        }
    ref = f"qb-tg-test-{action['request']}"
    try:
        async with httpx.AsyncClient(
            base_url="https://api.razorpay.com/v1", auth=auth, timeout=10, transport=transport
        ) as client:
            # Reconcile by unique reference before creating; repeated button taps reuse the link.
            response = await client.get("/payment_links", params={"reference_id": ref})
            response.raise_for_status()
            links = [
                link
                for link in response.json().get("payment_links", [])
                if link.get("reference_id") == ref
            ]
            if links:
                link = links[0]
            elif action["kind"] == "check":
                return {
                    **reply("No test payment has been started for this request."),
                    "chat_id": chat,
                }
            else:
                response = await client.post(
                    "/payment_links",
                    json={
                        "amount": amount,
                        "currency": "INR",
                        "accept_partial": False,
                        "reference_id": ref,
                        "description": "Quickbuddy TEST request — no real order or delivery",
                        "notify": {"sms": False, "email": False},
                        "reminder_enable": False,
                    },
                )
                response.raise_for_status()
                link = response.json()
            if (
                link.get("reference_id") != ref
                or link.get("amount") != amount
                or link.get("currency") != "INR"
            ):
                raise ValueError("Payment reference or amount mismatch")
            paid = link.get("status") == "paid" and link.get("amount_paid") == amount
            with store.db:
                store.db.execute(
                    "INSERT OR REPLACE INTO test_payments VALUES (?,?,?)",
                    (action["request"], chat, json.dumps(link)),
                )
            message = (
                "✅ TEST payment verified by Razorpay. No real order or delivery created."
                if paid
                else f"🧪 Razorpay TEST checkout · ₹{amount / 100:.2f}\n"
                "No real money or confirmed delivery.\n" + link.get("short_url", "")
            )
            response = reply(message, [f"Check payment {action['request']}", "Main menu"])
            if not paid and link.get("short_url", "").startswith("https://rzp.io/"):
                response["checkout_url"] = link["short_url"]
            return {**response, "chat_id": chat}
    except (httpx.HTTPError, ValueError, KeyError):
        return {
            **reply(
                "Test payment provider unavailable or status uncertain. "
                "Use Check payment before trying again. No payment success assumed.",
                [f"Check payment {action['request']}", "Main menu"],
            ),
            "chat_id": chat,
        }
