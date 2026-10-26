"""Short-lived, read-only context retrieval for role-specific AI assistants."""

from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, or_, select

from ai_platform.inference import service as ai_service
from backend.application.common import now, scoped
from backend.domain.rules import BusinessError
from backend.persistence import models as m
from backend.persistence.repositories import Repository


async def _active_user(db, actor):
    user = await db.get(m.User, UUID(actor.subject))
    if not user or user.status != "active":
        raise BusinessError("forbidden", "Access denied", 403)
    return user


def _scope_shape(request, expected):
    supplied = {
        key
        for key in ("city_id", "branch_id", "organization_id", "ticket_id")
        if getattr(request, key) is not None
    }
    allowed = {expected} if expected else set()
    if supplied != allowed:
        raise BusinessError("invalid_agent_scope", "Assistant scope does not match this role", 422)


async def context_for(db, actor, role, request):
    """Retrieve only the evidence the authenticated role can already read."""
    await _active_user(db, actor)
    if role == "customer":
        _scope_shape(request, "city_id")
        if request.city_id is None:
            raise BusinessError("city_required", "Select a delivery city to search", 422)
        city = await Repository(db).require(m.City, request.city_id)
        if not city.active:
            raise BusinessError("city_unavailable", "City is not active", 409)
        # Uses only public catalogue fields; descriptions, customer history and addresses are
        # intentionally excluded from external model context.
        query = (
            select(
                m.Product.name,
                m.Variant.name,
                m.Branch.name,
                m.Stock.on_hand,
                m.Stock.reserved,
                m.Price.amount,
                m.Price.currency,
            )
            .join(m.Variant, m.Variant.product_id == m.Product.id)
            .join(m.Stock, m.Stock.variant_id == m.Variant.id)
            .join(m.Branch, m.Branch.id == m.Stock.branch_id)
            .join(m.Price, m.Price.variant_id == m.Variant.id)
            .where(
                m.Product.active.is_(True),
                m.Branch.city_id == city.id,
                m.Branch.status == "approved",
                m.Branch.accepting_orders.is_(True),
                m.Stock.on_hand > m.Stock.reserved,
                m.Price.branch_id == m.Branch.id,
                m.Price.starts_at <= now(),
                (m.Price.ends_at.is_(None) | (m.Price.ends_at > now())),
            )
        )
        ignored = {"find", "near", "me", "show", "what", "the", "for", "with", "under", "available"}
        terms = [
            term.strip(".,!?\"'").replace("%", "")
            for term in request.question.split()
            if len(term.strip(".,!?\"'")) >= 3 and term.strip(".,!?\"'").lower() not in ignored
        ][:5]
        if terms:
            query = query.where(or_(*(m.Product.name.ilike("%" + term + "%") for term in terms)))
        rows = (await db.execute(query.order_by(m.Product.name).limit(10))).all()
        return {
            "scope": {"city_id": str(city.id), "timezone": city.timezone},
            "available_catalog_matches": [
                {
                    "product": product,
                    "variant": variant,
                    "merchant": branch,
                    "available_quantity": str(on_hand - reserved),
                    "price": str(price),
                    "currency": currency,
                }
                for product, variant, branch, on_hand, reserved, price, currency in rows
            ],
            "matched_count": len(rows),
            "data_source": "live_available_catalog",
        }

    if role == "merchant":
        _scope_shape(request, "branch_id")
        if request.branch_id is None:
            raise BusinessError("branch_required", "Select an authorized branch", 422)
        branch = await Repository(db).require(m.Branch, request.branch_id)
        await scoped(db, actor, "ai.read", branch.organization_id, branch.city_id, branch.id)
        since = now() - timedelta(days=1)
        sales = (
            await db.execute(
                select(
                    m.MerchantOrder.currency,
                    func.count(m.MerchantOrder.id),
                    func.coalesce(func.sum(m.MerchantOrder.total), 0),
                )
                .where(
                    m.MerchantOrder.branch_id == branch.id,
                    m.MerchantOrder.created_at >= since,
                    m.MerchantOrder.status.not_in(["cancelled", "rejected"]),
                )
                .group_by(m.MerchantOrder.currency)
            )
        ).all()
        unavailable = await db.scalar(
            select(func.count())
            .select_from(m.Stock)
            .where(m.Stock.branch_id == branch.id, m.Stock.on_hand <= m.Stock.reserved)
        )
        return {
            "branch_id": str(branch.id),
            "branch_name": branch.name,
            "range": "previous_24_hours",
            "sales_by_currency": [
                {"currency": currency, "orders": int(count), "gross": str(gross)}
                for currency, count, gross in sales
            ],
            "unavailable_stock_lines": int(unavailable or 0),
            "source": "merchant_orders_and_stock_balances",
        }

    if role == "pilot":
        _scope_shape(request, None)
        pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
        if not pilot:
            raise BusinessError(
                "pilot_profile_required", "No pilot profile is linked to this user", 403
            )
        rows = (
            await db.execute(
                select(m.DeliveryTask, m.Assignment, m.Branch.name)
                .join(m.Assignment, m.Assignment.task_id == m.DeliveryTask.id)
                .join(m.FulfillmentUnit, m.FulfillmentUnit.id == m.DeliveryTask.fulfillment_unit_id)
                .join(m.MerchantOrder, m.MerchantOrder.id == m.FulfillmentUnit.merchant_order_id)
                .join(m.Branch, m.Branch.id == m.MerchantOrder.branch_id)
                .where(
                    m.Assignment.pilot_id == pilot.id,
                    m.Assignment.status.in_(["accepted", "picked_up"]),
                    m.DeliveryTask.status.not_in(["delivered", "cancelled"]),
                )
                .order_by(m.DeliveryTask.created_at)
                .limit(10)
            )
        ).all()
        return {
            "pilot_state": pilot.state,
            "assigned_stops": [
                {"delivery_id": str(task.id), "status": task.status, "pickup_merchant": branch}
                for task, _assignment, branch in rows
            ],
            "source": "current_authoritative_assignments",
            "route_mutation_available": False,
        }

    if role == "city":
        _scope_shape(request, "city_id")
        if request.city_id is None:
            raise BusinessError("city_required", "Select an authorized city", 422)
        city = await Repository(db).require(m.City, request.city_id)
        await scoped(db, actor, "ai.read", city_id=city.id)
        counts = {}
        for status in ("unassigned", "offered", "assigned", "picked_up"):
            counts[status] = int(
                await db.scalar(
                    select(func.count())
                    .select_from(m.DeliveryTask)
                    .join(m.FulfillmentUnit)
                    .join(m.MerchantOrder)
                    .join(m.Branch)
                    .where(m.Branch.city_id == city.id, m.DeliveryTask.status == status)
                )
                or 0
            )
        forecast = await ai_service.city_demand_forecast(db, city)
        return {
            "city_id": str(city.id),
            "generated_at": now().isoformat(),
            "delivery_status_counts": counts,
            "demand_forecast": forecast["horizons"],
            "forecast_source": forecast["provenance"],
            "source_cutoff": forecast["source_cutoff"],
        }

    if role == "admin":
        _scope_shape(request, "organization_id")
        if request.organization_id is None:
            raise BusinessError("organization_required", "Select an authorized organization", 422)
        await scoped(db, actor, "finance.read", request.organization_id)
        org_orders = (
            select(m.MerchantOrder.order_id)
            .join(m.Branch, m.Branch.id == m.MerchantOrder.branch_id)
            .where(m.Branch.organization_id == request.organization_id)
            .distinct()
            .subquery()
        )
        rows = (
            await db.execute(
                select(
                    m.PaymentIntent.status,
                    m.PaymentIntent.currency,
                    func.count(),
                    func.sum(m.PaymentIntent.amount),
                )
                .join(org_orders, org_orders.c.order_id == m.PaymentIntent.order_id)
                .group_by(m.PaymentIntent.status, m.PaymentIntent.currency)
                .order_by(m.PaymentIntent.status, m.PaymentIntent.currency)
            )
        ).all()
        return {
            "organization_id": str(request.organization_id),
            "payment_intent_summary": [
                {"status": status, "currency": currency, "count": int(count), "amount": str(amount)}
                for status, currency, count, amount in rows
            ],
            "source": "authoritative_payment_intents",
            "accounting_note": (
                "This is payment-intent activity, not recognized revenue or a ledger balance."
            ),
        }

    if role == "support":
        _scope_shape(request, "ticket_id")
        if request.ticket_id is None:
            raise BusinessError("ticket_required", "Select an assigned support case", 422)
        ticket = await Repository(db).require(m.Ticket, request.ticket_id)
        from backend.api.v1.routes import _support_ticket_access

        await _support_ticket_access(db, actor, ticket)
        if ticket.assigned_to_id != UUID(actor.subject):
            raise BusinessError(
                "ticket_not_assigned", "Claim this case before using its copilot", 403
            )
        message_count = int(
            await db.scalar(
                select(func.count())
                .select_from(m.TicketMessage)
                .where(m.TicketMessage.ticket_id == ticket.id)
            )
            or 0
        )
        return {
            "ticket_id": str(ticket.id),
            "status": ticket.status,
            "message_count": message_count,
            "has_linked_order": ticket.order_id is not None,
            "customer_message_text_sent_to_model": False,
            "source": "assigned_support_ticket_metadata",
        }

    raise BusinessError("agent_not_found", "AI assistant is not available", 404)
