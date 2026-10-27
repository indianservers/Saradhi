"""Authoritative per-delivery grouping and configured delivery pricing."""

from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from backend.application.common import now
from backend.domain.rules import BusinessError, money
from backend.persistence.foundations import FOUNDATION_MODELS as F


async def delivery_rates(session, branches, currency):
    rules = F["finance.fee_rules"]
    rows = (
        await session.scalars(
            select(rules).where(
                rules.city_id.in_({b.city_id for b in branches.values()}),
                rules.currency_id == currency.id,
                rules.starts_at <= now(),
            )
        )
    ).all()
    result = {}
    for branch in branches.values():
        selected = []
        for name in (f"delivery:{branch.id}", "delivery"):
            eligible = [r for r in rows if r.city_id == branch.city_id and r.name == name]
            if eligible:
                latest = max(r.starts_at for r in eligible)
                selected = [r for r in eligible if r.starts_at == latest]
                break
        if len(selected) > 1:
            raise BusinessError("ambiguous_delivery_fee", "Multiple delivery rates apply", 409)
        if selected:
            rate = selected[0]
            if not rate.amount.is_finite() or rate.amount < 0:
                raise BusinessError("invalid_delivery_fee", "Invalid configured delivery rate", 409)
            result[str(branch.id)] = {
                "amount": money(rate.amount, currency.scale),
                "rule_id": str(rate.id),
            }
    return result


def group_deliveries(lines, branches, windows, rates, scale):
    groups = defaultdict(list)
    for line in lines:
        address = line.get("address") or {}
        groups[
            (line["branch_id"], line["window_id"], line["delivery_method"], address.get("id"))
        ].append(line)
    result = []
    for (branch_id, window_id, method, address_id), group in groups.items():
        branch, window = branches[UUID(branch_id)], windows[UUID(window_id)]
        rate = rates.get(branch_id)
        if method != "pickup" and rate is None:
            raise BusinessError(
                "delivery_fee_unavailable",
                f"Delivery pricing is not configured for {branch.name}; choose pickup",
                409,
            )
        fee = Decimal(0) if method == "pickup" else rate["amount"]
        subtotal = sum((Decimal(r["total"]) for r in group), Decimal(0))
        items = sum((Decimal(r["unit_price"]) * Decimal(r["quantity"]) for r in group), Decimal(0))
        result.append(
            {
                "branch_id": branch_id,
                "branch_name": branch.name,
                "window_id": window_id,
                "delivery_method": method,
                "address_id": address_id,
                "line_ids": [r["cart_item_id"] for r in group],
                "items": str(money(items, scale)),
                "extras": str(money(subtotal - items, scale)),
                "delivery_fee": str(money(fee, scale)),
                "delivery_rule_id": rate["rule_id"] if method != "pickup" else None,
                "taxes": "0",
                "discounts": "0",
                "total": str(money(subtotal + fee, scale)),
                "estimated_arrival_start": window.starts_at.isoformat(),
                "estimated_arrival_end": window.ends_at.isoformat(),
                "estimate_basis": "merchant_scheduled_window",
            }
        )
    return result
