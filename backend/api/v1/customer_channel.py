"""Authenticated live catalog enrichment; merchant writes retain organization scopes."""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import delete, select

from backend.api.v1.dependencies import DB, Actor
from backend.application.common import add, branch_scope, scoped
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository

router = APIRouter(prefix="/api/v1/channel", tags=["Customer channels"])


@router.get("/merchant-orders/{order_id}/items")
async def merchant_items(order_id: UUID, actor: Actor, db: DB):
    order = await Repository(db).require(m.MerchantOrder, order_id)
    await branch_scope(db, actor, order.branch_id, "merchant.write")
    items = (
        await db.scalars(select(m.OrderItem).where(m.OrderItem.merchant_order_id == order.id))
    ).all()
    return {
        "items": [
            {
                "id": item.id,
                "name": item.product_name,
                "variant": item.variant_name,
                "quantity": str(item.quantity),
                "addons": item.snapshot.get("addons", []),
                "preparation_notes": item.snapshot.get("preparation_notes", ""),
            }
            for item in items
        ]
    }


class OptionValue(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price_delta: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class OptionGroup(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    minimum: int = Field(default=0, ge=0, le=10)
    maximum: int = Field(default=1, ge=1, le=10)
    values: list[OptionValue] = Field(min_length=1, max_length=30)


class ProductDetails(BaseModel):
    ingredients: list[str] | None = Field(default=None, max_length=60)
    image_url: HttpUrl | None = None
    dietary: list[Literal["vegetarian", "vegan", "gluten_free", "halal", "jain"]] = Field(
        default_factory=list, max_length=5
    )
    allergens: list[str] = Field(default_factory=list, max_length=30)
    allergens_reviewed: bool = False
    groups: list[OptionGroup] = Field(default_factory=list, max_length=10)


@router.put("/products/{product_id}/details")
async def write_details(product_id: UUID, body: ProductDetails, actor: Actor, db: DB):
    from backend.domain.rules import BusinessError

    product = await Repository(db).require(m.Product, product_id)
    await scoped(db, actor, "catalog.write", product.organization_id)
    detail = await db.scalar(
        select(m.ProductCustomerDetails)
        .where(m.ProductCustomerDetails.product_id == product_id)
        .with_for_update()
    )
    if not detail:
        detail = await add(db, m.ProductCustomerDetails, product_id=product_id)
    detail.ingredients = body.ingredients
    detail.image_url = str(body.image_url) if body.image_url else None
    detail.allergens_reviewed = body.allergens_reviewed
    for key in (
        "catalog.dietary_attributes",
        "catalog.product_allergens",
        "catalog.product_customizations",
    ):
        await db.execute(delete(F[key]).where(F[key].product_id == product_id))
    for code in set(body.dietary):
        await add(db, F["catalog.dietary_attributes"], product_id=product_id, dietary_code=code)
    for code in set(body.allergens):
        await add(
            db,
            F["catalog.product_allergens"],
            product_id=product_id,
            allergen_code=code[:80],
            may_contain=True,
        )
    for group in body.groups:
        if group.minimum > group.maximum or group.maximum > len(group.values):
            raise BusinessError("invalid_options", "Invalid option group bounds", 422)
        group_row = await add(
            db,
            F["catalog.option_groups"],
            organization_id=product.organization_id,
            name=group.name,
            minimum_selections=group.minimum,
            maximum_selections=group.maximum,
        )
        await add(
            db,
            F["catalog.product_customizations"],
            product_id=product_id,
            option_group_id=group_row.id,
            required=group.minimum > 0,
        )
        for value in group.values:
            await add(
                db,
                F["catalog.option_values"],
                group_id=group_row.id,
                name=value.name,
                price_delta=value.price_delta,
            )
    return {"saved": True, "product_id": product_id}


@router.get("/catalog")
async def catalog(
    actor: Actor,
    db: DB,
    city_id: UUID | None = None,
    branch_id: UUID | None = None,
    cursor: str | None = None,
    limit: int = Query(default=100, ge=1, le=100),
):
    from backend.api.v1.routes import customer_catalog

    page = await customer_catalog(
        actor,
        db,
        city_id=city_id,
        branch_id=branch_id,
        category_id=None,
        merchant_type="food",
        q=None,
        cursor=cursor,
        limit=limit,
    )
    product_ids = {row.product_id for row in page["items"]}
    details = {
        row.product_id: row
        for row in (
            await db.scalars(
                select(m.ProductCustomerDetails).where(
                    m.ProductCustomerDetails.product_id.in_(product_ids)
                )
            )
        ).all()
    }
    dietary, allergens, groups = {}, {}, {}
    for key, target, code in (
        ("catalog.dietary_attributes", dietary, "dietary_code"),
        ("catalog.product_allergens", allergens, "allergen_code"),
    ):
        for row in (
            await db.scalars(select(F[key]).where(F[key].product_id.in_(product_ids)))
        ).all():
            target.setdefault(row.product_id, []).append(getattr(row, code))
    Link, Group, Value = (
        F[k]
        for k in (
            "catalog.product_customizations",
            "catalog.option_groups",
            "catalog.option_values",
        )
    )
    group_rows = (
        await db.execute(
            select(Link, Group)
            .join(Group, Group.id == Link.option_group_id)
            .where(Link.product_id.in_(product_ids))
        )
    ).all()
    values = (
        await db.scalars(select(Value).where(Value.group_id.in_({g.id for _, g in group_rows})))
    ).all()
    for link, group in group_rows:
        groups.setdefault(link.product_id, []).append(
            {
                "id": group.id,
                "name": group.name,
                "minimum": group.minimum_selections,
                "maximum": group.maximum_selections,
                "values": [
                    {"id": v.id, "name": v.name, "price_delta": str(v.price_delta)}
                    for v in values
                    if v.group_id == group.id
                ],
            }
        )
    result = []
    for row in page["items"]:
        detail = details.get(row.product_id)
        availability = F["catalog.product_branch_availability"]
        disabled = await db.scalar(
            select(availability.id).where(
                availability.branch_id == row.branch_id,
                availability.variant_id == row.variant_id,
                availability.available.is_(False),
            )
        )
        if disabled:
            continue
        result.append(
            {
                **row.model_dump(mode="json"),
                "dietary": dietary.get(row.product_id, []),
                "allergens": allergens.get(row.product_id, []),
                "groups": groups.get(row.product_id, []),
                "ingredients": detail.ingredients if detail else None,
                "allergens_reviewed": detail.allergens_reviewed if detail else False,
                "image_url": detail.image_url if detail else None,
            }
        )
    return {"items": result, "next_cursor": page["next_cursor"]}


class BranchDeliveryFee(BaseModel):
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@router.put("/branches/{branch_id}/delivery-fee")
async def set_delivery_fee(branch_id: UUID, body: BranchDeliveryFee, actor: Actor, db: DB):
    from backend.application.common import now
    from backend.domain.rules import BusinessError

    branch = await branch_scope(db, actor, branch_id, "catalog.write", lock=True)
    currency = await db.scalar(select(m.Currency).where(m.Currency.code == body.currency))
    if currency is None:
        raise BusinessError("unknown_currency", "Currency is not configured", 422)
    row = await add(
        db,
        F["finance.fee_rules"],
        city_id=branch.city_id,
        currency_id=currency.id,
        name=f"delivery:{branch.id}",
        amount=body.amount,
        starts_at=now(),
    )
    return {"id": row.id, "branch_id": branch.id, "amount": row.amount, "currency": currency.code}
