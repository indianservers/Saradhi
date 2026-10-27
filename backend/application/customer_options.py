"""Merchant-owned option validation and authoritative per-unit option pricing."""

from collections import Counter
from decimal import Decimal

from sqlalchemy import select

from backend.domain.rules import BusinessError
from backend.persistence.foundations import FOUNDATION_MODELS as F


async def priced_options(session, product, item):
    Choice, Value, Group, Link = (
        F[key]
        for key in (
            "commerce.cart_item_options",
            "catalog.option_values",
            "catalog.option_groups",
            "catalog.product_customizations",
        )
    )
    links = (
        await session.execute(
            select(Link, Group)
            .join(Group, Group.id == Link.option_group_id)
            .where(Link.product_id == product.id)
        )
    ).all()
    options = (
        await session.execute(
            select(Choice, Value)
            .join(Value, Value.id == Choice.option_id)
            .where(Choice.cart_item_id == item.id)
        )
    ).all()
    groups = {group.id: (link, group) for link, group in links}
    counts = Counter()
    addons = []
    total = Decimal(0)
    for chosen, value in options:
        if (
            value.group_id not in groups
            or groups[value.group_id][1].organization_id != product.organization_id
        ):
            raise BusinessError(
                "invalid_option", "Customization is not offered for this product", 422
            )
        counts[value.group_id] += chosen.quantity
        total += value.price_delta * chosen.quantity
        addons.append(
            {
                "option_id": str(value.id),
                "name": value.name,
                "quantity": chosen.quantity,
                "unit_price": str(value.price_delta),
            }
        )
    for group_id, (link, group) in groups.items():
        minimum = max(group.minimum_selections, 1 if link.required else 0)
        if not minimum <= counts[group_id] <= group.maximum_selections:
            raise BusinessError(
                "option_selection_required",
                f"Choose {minimum}–{group.maximum_selections} options for {group.name}",
                422,
            )
    return total, addons
