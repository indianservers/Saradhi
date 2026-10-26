"""Readiness checks and audited activation for newly configured marketplace cities."""

from sqlalchemy import func, select

from backend.application.common import audit, now
from backend.domain.rules import BusinessError
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository


async def readiness(session, city):
    active_zones = select(m.Zone.id).where(m.Zone.city_id == city.id, m.Zone.active.is_(True))
    zone_count = int(
        await session.scalar(select(func.count()).select_from(active_zones.subquery())) or 0
    )
    category_count = int(
        await session.scalar(
            select(func.count())
            .select_from(m.ZoneCategory)
            .where(
                m.ZoneCategory.zone_id.in_(active_zones),
                m.ZoneCategory.enabled.is_(True),
            )
        )
        or 0
    )
    capability = F["merchant.merchant_fulfillment_capabilities"]
    eligible_branch_count = int(
        await session.scalar(
            select(func.count(func.distinct(m.Branch.id)))
            .select_from(m.Branch)
            .join(m.Brand, m.Brand.id == m.Branch.brand_id)
            .join(m.Product, m.Product.organization_id == m.Branch.organization_id)
            .join(m.Category, m.Category.id == m.Product.category_id)
            .join(m.Variant, m.Variant.product_id == m.Product.id)
            .join(
                m.Stock,
                (m.Stock.variant_id == m.Variant.id) & (m.Stock.branch_id == m.Branch.id),
            )
            .join(
                m.ZoneCategory,
                (m.ZoneCategory.category_id == m.Product.category_id)
                & m.ZoneCategory.enabled.is_(True),
            )
            .join(m.Zone, m.Zone.id == m.ZoneCategory.zone_id)
            .join(m.Price, m.Price.variant_id == m.Variant.id)
            .join(m.Window, m.Window.branch_id == m.Branch.id)
            .join(capability, capability.branch_id == m.Branch.id)
            .where(
                m.Branch.city_id == city.id,
                m.Branch.status == "approved",
                m.Branch.accepting_orders.is_(True),
                m.Zone.active.is_(True),
                m.Zone.city_id == city.id,
                m.Product.active.is_(True),
                m.Category.regulated.is_(False),
                capability.method == "pickup",
                capability.active.is_(True),
                m.Stock.on_hand > m.Stock.reserved,
                m.Price.branch_id == m.Branch.id,
                m.Price.starts_at <= now(),
                (m.Price.ends_at.is_(None) | (m.Price.ends_at > now())),
                m.Window.starts_at > now(),
                m.Window.reserved < m.Window.capacity,
            )
        )
        or 0
    )
    missing = []
    if zone_count == 0:
        missing.append("active_service_zone")
    if category_count == 0:
        missing.append("enabled_zone_category")
    if eligible_branch_count == 0:
        missing.append("approved_merchant_with_available_stock_price_and_future_capacity")
    return {
        "city_id": str(city.id),
        "launch_state": "active" if city.active else "draft",
        "ready": not missing,
        "active_zones": zone_count,
        "enabled_zone_categories": category_count,
        "eligible_branches": eligible_branch_count,
        "missing_requirements": missing,
        "regulated_categories_enabled": False,
    }


async def activate(session, actor, city_id, request_id):
    city = await Repository(session).require(m.City, city_id, lock=True)
    result = await readiness(session, city)
    if not result["ready"]:
        raise BusinessError(
            "city_not_ready",
            "City requires a zone, enabled category and approved merchant capacity",
            409,
        )
    if not city.active:
        city.active = True
        version = await _next_version(session, city.id)
        await audit(
            session,
            actor,
            "city.activate",
            city.id,
            request_id,
            previous="draft",
            current="active",
            version=version,
        )
    return result | {"launch_state": "active"}


async def deactivate(session, actor, city_id, request_id):
    city = await Repository(session).require(m.City, city_id, lock=True)
    if city.active:
        city.active = False
        version = await _next_version(session, city.id)
        await audit(
            session,
            actor,
            "city.deactivate",
            city.id,
            request_id,
            previous="active",
            current="suspended",
            version=version,
        )
    return {"city_id": str(city.id), "launch_state": "suspended", "active": city.active}


async def _next_version(session, city_id):
    return (
        int(
            await session.scalar(
                select(func.count())
                .select_from(m.AuditEvent)
                .where(
                    m.AuditEvent.resource_id == city_id,
                    m.AuditEvent.action.in_(["city.create", "city.activate", "city.deactivate"]),
                )
            )
            or 0
        )
        + 1
    )
