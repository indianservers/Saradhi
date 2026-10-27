from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select, text, tuple_, update
from sqlalchemy.dialects.postgresql import insert

from ai_platform.inference.service import preparation_rule
from backend.application import batches
from backend.application.common import add, audit, branch_scope, event, now, owned
from backend.application.customer_options import priced_options
from backend.domain.rules import BusinessError, money, transition
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository


async def serviceable(session, branch, window, method, address, category_id):
    city = await session.get(m.City, branch.city_id)
    instant = window.starts_at
    if not city.active or branch.status != "approved" or not branch.accepting_orders:
        raise BusinessError("unavailable_branch", "Merchant branch or city is unavailable")
    if window.branch_id != branch.id or window.ends_at <= now() or window.starts_at < now():
        raise BusinessError("invalid_window", "A future window for this branch is required")
    local = instant.astimezone(ZoneInfo(city.timezone))
    Calendar, Holiday = F["geo.operating_calendars"], F["geo.holidays"]
    if await session.scalar(
        select(Holiday.id)
        .join(Calendar)
        .where(
            Calendar.city_id == city.id,
            Holiday.local_date == local.date(),
            Holiday.closed.is_(True),
        )
    ):
        raise BusinessError("city_holiday", "City operations are closed for this local date")
    hours = (
        await session.scalars(
            select(m.OperatingHour).where(
                m.OperatingHour.branch_id == branch.id, m.OperatingHour.weekday == local.weekday()
            )
        )
    ).all()
    Special, Closure = (
        F["merchant.merchant_special_hours"],
        F["merchant.merchant_temporary_closures"],
    )
    special = (
        await session.scalars(
            select(Special).where(
                Special.branch_id == branch.id, Special.local_date == local.date()
            )
        )
    ).all()
    candidates = special if special else hours
    end_local = window.ends_at.astimezone(ZoneInfo(city.timezone))
    if end_local.date() != local.date() or not any(
        h.opens_at <= local.time() and end_local.time() <= h.closes_at for h in candidates
    ):
        raise BusinessError("merchant_closed", "Delivery window is outside branch operating hours")
    closed = await session.scalar(
        select(Closure.id).where(
            Closure.branch_id == branch.id,
            Closure.starts_at < window.ends_at,
            Closure.ends_at > instant,
        )
    )
    if closed:
        raise BusinessError("merchant_closed", "Merchant is temporarily closed")
    if window.reserved >= window.capacity:
        raise BusinessError("slot_full", "Delivery window capacity is exhausted")
    capability = F["merchant.merchant_fulfillment_capabilities"]
    if not await session.scalar(
        select(capability.id).where(
            capability.branch_id == branch.id,
            capability.method == method,
            capability.active.is_(True),
        )
    ):
        raise BusinessError(
            "unsupported_fulfillment", "Branch does not offer this fulfillment method"
        )
    category = await session.get(m.Category, category_id)
    if category.regulated:
        raise BusinessError(
            "regulated_checkout_unavailable",
            "Regulated categories require approved licensing and prescription workflow",
        )
    if method == "pickup":
        return
    if not address or address.city_id != city.id:
        raise BusinessError("unserviceable", "Destination must be in the branch service city")
    extension = await session.scalar(
        text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='postgis')")
    )
    spatial = await session.scalar(
        text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='geo' AND table_name='delivery_service_areas' "
            "AND column_name='boundary')"
        )
    )
    if not extension or not spatial:
        raise BusinessError(
            "spatial_unavailable",
            "PostGIS and the optional spatial migration are required for delivery serviceability",
            503,
        )
    area = await session.scalar(
        text("""
        SELECT a.id FROM geo.delivery_service_areas a
        JOIN geo.service_zones z ON z.id = a.zone_id
        JOIN geo.zone_service_categories c ON c.zone_id = z.id
        JOIN merchant.merchant_service_areas ma ON ma.area_id = a.id
        JOIN geo.zone_delivery_policies dp ON dp.zone_id=z.id
        JOIN geo.zone_capacity_settings cs ON cs.zone_id=z.id
        WHERE z.active AND z.city_id=:city AND c.enabled AND c.category_id=:category
          AND ma.branch_id=:branch AND ma.category_id=:category AND ma.delivery_method=:method
          AND dp.active AND dp.delivery_method=:method AND a.spatial_ready
          AND ST_Covers(a.boundary, ST_SetSRID(ST_MakePoint(:lon,:lat),4326))
          AND ST_DWithin(ST_SetSRID(ST_MakePoint(:blon,:blat),4326)::geography,
                         ST_SetSRID(ST_MakePoint(:lon,:lat),4326)::geography,dp.maximum_distance_m)
          AND (SELECT count(*) FROM fulfillment.delivery_tasks t
               JOIN fulfillment.fulfillment_units u ON u.id=t.fulfillment_unit_id
               JOIN commerce.merchant_orders mo ON mo.id=u.merchant_order_id
               JOIN merchant.merchant_branches b ON b.id=mo.branch_id
               WHERE b.city_id=z.city_id AND t.status IN ('assigned','picked_up'))
              < cs.maximum_active_tasks
        ORDER BY a.id LIMIT 1
    """),
        {
            "city": city.id,
            "category": category_id,
            "branch": branch.id,
            "method": method,
            "lat": address.latitude,
            "lon": address.longitude,
            "blat": branch.latitude,
            "blon": branch.longitude,
        },
    )
    if not area:
        raise BusinessError(
            "unserviceable", "Destination, category, delivery policy or capacity is not serviceable"
        )


async def cart_context(session, actor, cart_id, lock=True):
    cart = await Repository(session).require(m.Cart, cart_id, lock=lock)
    owned(actor, cart.user_id)
    if cart.status != "open":
        raise BusinessError("cart_closed", "Cart is already confirmed")
    return cart


async def add_item(session, actor, cart_id, values):
    cart = await cart_context(session, actor, cart_id)
    if values.address_id:
        address = await Repository(session).require(m.Address, values.address_id)
        owned(actor, address.user_id)
    await Repository(session).require(m.Branch, values.branch_id)
    await Repository(session).require(m.Variant, values.variant_id)
    window = await Repository(session).require(m.Window, values.window_id)
    if window.branch_id != values.branch_id:
        raise BusinessError("invalid_window", "Window belongs to another branch", 422)
    item = await add(
        session, m.CartItem, cart_id=cart.id, **values.model_dump(exclude={"option_ids"})
    )
    for option_id in set(values.option_ids):
        await add(
            session,
            F["commerce.cart_item_options"],
            cart_item_id=item.id,
            option_id=option_id,
            quantity=1,
        )
    cart.version += 1
    return item


async def make_quote(session, actor, cart_id):
    cart = await cart_context(session, actor, cart_id)
    rows = (
        await session.execute(
            select(m.CartItem, m.Variant, m.Product, m.Branch, m.Window)
            .join(m.Variant, m.Variant.id == m.CartItem.variant_id)
            .join(m.Product, m.Product.id == m.Variant.product_id)
            .join(m.Branch, m.Branch.id == m.CartItem.branch_id)
            .join(m.Window, m.Window.id == m.CartItem.window_id)
            .where(m.CartItem.cart_id == cart.id)
            .order_by(m.CartItem.id)
        )
    ).all()
    if not rows:
        raise BusinessError("empty_cart", "Add at least one item", 422)
    if len(rows) > 100:
        raise BusinessError("cart_limit", "At most 100 cart lines are supported", 422)
    pairs = {(branch.id, variant.id) for _, variant, _, branch, _ in rows}
    product_ids = {product.id for _, _, product, _, _ in rows}
    address_ids = {item.address_id for item, _, _, _, _ in rows if item.address_id}
    addresses = {
        row.id: row
        for row in (
            await session.scalars(select(m.Address).where(m.Address.id.in_(address_ids)))
        ).all()
    }
    Availability, Tax = (
        F["catalog.product_branch_availability"],
        F["catalog.product_tax_categories"],
    )
    availability_map = {
        (row.branch_id, row.variant_id): row.available
        for row in (
            await session.scalars(
                select(Availability).where(
                    tuple_(Availability.branch_id, Availability.variant_id).in_(pairs)
                )
            )
        ).all()
    }
    taxable = set(
        (await session.scalars(select(Tax.product_id).where(Tax.product_id.in_(product_ids)))).all()
    )
    earliest = min(window.starts_at for *_, window in rows)
    latest = max(window.starts_at for *_, window in rows)
    candidate_prices = (
        await session.scalars(
            select(m.Price).where(
                tuple_(m.Price.branch_id, m.Price.variant_id).in_(pairs),
                m.Price.starts_at <= latest,
                or_(m.Price.ends_at.is_(None), m.Price.ends_at > earliest),
            )
        )
    ).all()
    price_map = defaultdict(list)
    for price in candidate_prices:
        price_map[(price.branch_id, price.variant_id)].append(price)
    currency_map = {
        row.code: row
        for row in (
            await session.scalars(
                select(m.Currency).where(
                    m.Currency.code.in_({price.currency for price in candidate_prices})
                )
            )
        ).all()
    }
    checked_service = set()
    currencies, lines = set(), []
    for item, variant, product, branch, window in rows:
        if product.organization_id != branch.organization_id or not product.active:
            raise BusinessError("invalid_catalog", "Product is unavailable at this merchant")
        if product.variable_weight:
            raise BusinessError(
                "weighing_workflow_required",
                "Variable weight checkout requires final weighing and payment authorization",
            )
        if product.unit == "each" and item.quantity != item.quantity.to_integral():
            raise BusinessError(
                "invalid_quantity", "Each-based products require integral quantities", 422
            )
        if availability_map.get((branch.id, variant.id)) is False:
            raise BusinessError("product_unavailable", "Product is disabled at this branch")
        if product.id in taxable:
            raise BusinessError(
                "tax_calculation_required",
                "Configured tax products require an approved tax calculator",
            )
        address = addresses.get(item.address_id)
        if address:
            owned(actor, address.user_id)
        service_key = (
            branch.id,
            window.id,
            item.delivery_method,
            item.address_id,
            product.category_id,
        )
        if service_key not in checked_service:
            await serviceable(
                session, branch, window, item.delivery_method, address, product.category_id
            )
            checked_service.add(service_key)
        prices = [
            price
            for price in price_map[(branch.id, variant.id)]
            if price.starts_at <= window.starts_at
            and (price.ends_at is None or price.ends_at > window.starts_at)
        ]
        if len(prices) != 1:
            raise BusinessError(
                "price_unavailable", "Exactly one authorized branch price must apply"
            )
        price = prices[0]
        currency = currency_map[price.currency]
        currencies.add(price.currency)
        option_amount, addons = await priced_options(session, product, item)
        amount = money((price.amount + option_amount) * item.quantity, currency.scale)
        lines.append(
            {
                "cart_item_id": str(item.id),
                "branch_id": str(branch.id),
                "variant_id": str(variant.id),
                "product_name": product.name,
                "variant_name": variant.name,
                "quantity": str(item.quantity),
                "unit": product.unit,
                "unit_price": str(price.amount),
                "price_id": str(price.id),
                "price_book_id": str(price.price_book_id) if price.price_book_id else None,
                "category_id": str(product.category_id),
                "currency": price.currency,
                "total": str(amount),
                "window_id": str(window.id),
                "delivery_method": item.delivery_method,
                "addons": addons,
                "preparation_notes": item.preparation_notes,
                "discounts": [],
                "taxes": [],
                "address": {
                    "id": str(address.id),
                    "address_text": address.address_text,
                    "latitude": str(address.latitude),
                    "longitude": str(address.longitude),
                }
                if address
                else None,
            }
        )
    if len(currencies) != 1:
        raise BusinessError("mixed_currency_checkout", "Split checkout by currency", 422)
    from backend.application.checkout_groups import delivery_rates, group_deliveries

    branches = {branch.id: branch for _, _, _, branch, _ in rows}
    windows = {window.id: window for _, _, _, _, window in rows}
    currency = currency_map[next(iter(currencies))]
    delivery_branches = {
        UUID(line["branch_id"]): branches[UUID(line["branch_id"])]
        for line in lines
        if line["delivery_method"] != "pickup"
    }
    rates = await delivery_rates(session, delivery_branches, currency) if delivery_branches else {}
    shipments = group_deliveries(lines, branches, windows, rates, currency.scale)
    total = sum((Decimal(group["total"]) for group in shipments), Decimal(0))
    quote = await add(
        session,
        m.Quote,
        cart_id=cart.id,
        user_id=UUID(actor.subject),
        cart_version=cart.version,
        currency=next(iter(currencies)),
        total=total,
        snapshot={"lines": lines, "shipments": shipments},
        expires_at=now() + timedelta(minutes=5),
    )
    return quote


async def confirm(session, actor, quote_id, key, request_id):
    # ON CONFLICT waits for a racing transaction. Same user/key locks serialize safely.
    fingerprint = str(quote_id)
    await session.execute(
        insert(m.Idempotency)
        .values(user_id=UUID(actor.subject), key=key, fingerprint=fingerprint)
        .on_conflict_do_nothing(index_elements=["user_id", "key"])
    )
    idem = await session.scalar(
        select(m.Idempotency)
        .where(m.Idempotency.user_id == UUID(actor.subject), m.Idempotency.key == key)
        .with_for_update()
    )
    if idem.fingerprint != fingerprint:
        raise BusinessError(
            "idempotency_conflict", "Idempotency key was used for a different quote"
        )
    if idem.order_id:
        return await Repository(session).require(m.Order, idem.order_id)
    quote = await Repository(session).require(m.Quote, quote_id, lock=True)
    owned(actor, quote.user_id)
    cart = await cart_context(session, actor, quote.cart_id)
    if quote.expires_at <= now() or quote.consumed_at or quote.cart_version != cart.version:
        raise BusinessError("stale_quote", "Quote expired, was consumed, or cart changed")
    # Revalidate authorization, merchant, destination and prices at confirmation.
    fresh = await make_quote(session, actor, cart.id)
    if fresh.snapshot != quote.snapshot or fresh.total != quote.total:
        raise BusinessError("price_changed", "Quote no longer matches current branch prices")
    await session.delete(fresh)
    lines = quote.snapshot["lines"]
    # Stable global lock order reduces stock/slot deadlocks across overlapping carts.
    stocks = {}
    for branch_id, variant_id in sorted(
        {(line["branch_id"], line["variant_id"]) for line in lines}
    ):
        stock = await session.scalar(
            select(m.Stock)
            .where(m.Stock.branch_id == UUID(branch_id), m.Stock.variant_id == UUID(variant_id))
            .with_for_update()
        )
        if not stock:
            raise BusinessError("out_of_stock", "No inventory is configured")
        stocks[(branch_id, variant_id)] = stock
    groups = defaultdict(list)
    for line in lines:
        groups[
            (
                line["branch_id"],
                line["window_id"],
                line["delivery_method"],
                line["address"]["id"] if line["address"] else None,
            )
        ].append(line)
    for window_id in sorted({key[1] for key in groups}):
        count = sum(1 for group in groups if group[1] == window_id)
        reserved = await session.scalar(
            update(m.Window)
            .where(m.Window.id == UUID(window_id), m.Window.reserved + count <= m.Window.capacity)
            .values(reserved=m.Window.reserved + count)
            .returning(m.Window.id)
        )
        if not reserved:
            raise BusinessError("slot_full", "Concurrent checkout exhausted the delivery slot")
    order = await add(
        session,
        m.Order,
        user_id=UUID(actor.subject),
        quote_id=quote.id,
        currency=quote.currency,
        total=quote.total,
    )
    delivery_amount = sum(
        (Decimal(s["delivery_fee"]) for s in quote.snapshot.get("shipments", [])), Decimal(0)
    )
    if delivery_amount:
        currency = await session.scalar(select(m.Currency).where(m.Currency.code == quote.currency))
        await add(
            session,
            F["commerce.order_amount_breakdowns"],
            order_id=order.id,
            currency_id=currency.id,
            kind="delivery",
            amount=delivery_amount,
        )
    merchant_orders = {}
    for (branch_id, window_id, method, _), group in groups.items():
        if branch_id not in merchant_orders:
            subtotal = sum(
                (Decimal(line["total"]) for line in lines if line["branch_id"] == branch_id),
                Decimal(0),
            )
            merchant_orders[branch_id] = await add(
                session,
                m.MerchantOrder,
                order_id=order.id,
                branch_id=UUID(branch_id),
                currency=order.currency,
                total=subtotal,
            )
        merchant_order = merchant_orders[branch_id]
        unit = await add(
            session,
            m.FulfillmentUnit,
            merchant_order_id=merchant_order.id,
            window_id=UUID(window_id),
            delivery_method=method,
            address_snapshot=group[0]["address"],
        )
        for line in group:
            item = await add(
                session,
                m.OrderItem,
                merchant_order_id=merchant_order.id,
                fulfillment_unit_id=unit.id,
                variant_id=UUID(line["variant_id"]),
                product_name=line["product_name"],
                variant_name=line["variant_name"],
                unit=line["unit"],
                quantity=Decimal(line["quantity"]),
                unit_price=Decimal(line["unit_price"]),
                total=Decimal(line["total"]),
                snapshot=line,
            )
            stock = stocks[(branch_id, line["variant_id"])]
            quantity = Decimal(line["quantity"])
            changed = await session.scalar(
                update(m.Stock)
                .where(m.Stock.id == stock.id, m.Stock.on_hand - m.Stock.reserved >= quantity)
                .values(reserved=m.Stock.reserved + quantity, version=m.Stock.version + 1)
                .returning(m.Stock.id)
            )
            if not changed:
                raise BusinessError("out_of_stock", "Insufficient sellable stock")
            reservation = await add(
                session,
                m.Reservation,
                stock_id=stock.id,
                order_item_id=item.id,
                quantity=quantity,
                expires_at=now() + timedelta(minutes=15),
            )
            stock_branch = await session.get(m.Branch, UUID(branch_id))
            stock_city = await session.get(m.City, stock_branch.city_id)
            delivery_window = await session.get(m.Window, UUID(window_id))
            await batches.allocate(
                session,
                reservation,
                delivery_window.starts_at.astimezone(ZoneInfo(stock_city.timezone)).date(),
            )
            await add(
                session,
                m.StockMovement,
                stock_id=stock.id,
                reservation_id=reservation.id,
                quantity=quantity,
                kind="reserve",
                idempotency_key=f"reserve:{item.id}",
                actor_id=UUID(actor.subject),
            )
            await event(
                session, "inventory.reserved", reservation.id, request_id, order_id=order.id
            )
        await add(session, m.DeliveryTask, fulfillment_unit_id=unit.id)
    quote.consumed_at, cart.status = now(), "confirmed"
    idem.order_id = order.id
    await add(
        session,
        m.OrderHistory,
        order_id=order.id,
        previous=None,
        current="confirmed",
        actor_id=UUID(actor.subject),
    )
    await event(session, "order.created", order.id, request_id, user_id=actor.subject)
    await event(session, "order.confirmed", order.id, request_id)
    return order


async def release_reservation(session, reservation, actor_id, request_id):
    # Caller must hold the reservation row lock. Atomic transition prevents double release.
    if reservation.status != "reserved":
        return
    await session.execute(
        update(m.Stock)
        .where(m.Stock.id == reservation.stock_id)
        .values(reserved=m.Stock.reserved - reservation.quantity, version=m.Stock.version + 1)
    )
    await batches.finish(session, reservation)
    reservation.status = "released"
    await add(
        session,
        m.StockMovement,
        stock_id=reservation.stock_id,
        reservation_id=reservation.id,
        quantity=-reservation.quantity,
        kind="release",
        idempotency_key=f"release:{reservation.id}",
        actor_id=actor_id,
    )
    await event(session, "inventory.released", reservation.id, request_id)


async def _ensure_kitchen_tasks(session, child, branch):
    """Create immutable per-line prep work plus a packaging gate in the order transaction."""
    existing = await session.scalar(
        select(m.KitchenTask.id).where(m.KitchenTask.merchant_order_id == child.id).limit(1)
    )
    if existing:
        return
    station_rows = {}
    for name, packaging, capacity in (
        ("Main Kitchen", False, 8),
        ("Packaging", True, 4),
    ):
        await session.execute(
            insert(m.KitchenStation)
            .values(
                id=uuid4(),
                branch_id=branch.id,
                name=name,
                is_packaging=packaging,
                max_concurrent=capacity,
                active=True,
                version=1,
            )
            .on_conflict_do_nothing(index_elements=["branch_id", "name"])
        )
        station_rows[name] = await session.scalar(
            select(m.KitchenStation)
            .where(m.KitchenStation.branch_id == branch.id, m.KitchenStation.name == name)
            .with_for_update()
        )
    items = (
        await session.scalars(
            select(m.OrderItem)
            .where(m.OrderItem.merchant_order_id == child.id)
            .order_by(m.OrderItem.id)
        )
    ).all()
    if not items:
        raise BusinessError("kitchen_items_missing", "Merchant order contains no preparation items")
    queue_depth = await session.scalar(
        select(func.count())
        .select_from(m.MerchantOrder)
        .where(
            m.MerchantOrder.branch_id == branch.id,
            m.MerchantOrder.status.in_(["accepted", "preparing"]),
        )
    )
    estimate = preparation_rule(len(items), int(queue_depth or 0))
    target = now() + timedelta(minutes=estimate["expected_duration_minutes"])
    preparation_tasks = []
    for item in items:
        preparation_tasks.append(
            await add(
                session,
                m.KitchenTask,
                merchant_order_id=child.id,
                order_item_id=item.id,
                branch_id=branch.id,
                station_id=station_rows["Main Kitchen"].id,
                task_key=f"item:{item.id}:prep",
                task_type="prep",
                label=f"{item.product_name} · {item.variant_name}",
                quantity=item.quantity,
                status="pending",
                version=1,
                target_completed_at=target,
                estimate_provenance=estimate["provenance"],
                estimate_model_version=estimate["model_version"],
            )
        )
    packing = await add(
        session,
        m.KitchenTask,
        merchant_order_id=child.id,
        order_item_id=None,
        branch_id=branch.id,
        station_id=station_rows["Packaging"].id,
        task_key="order:packing",
        task_type="packing",
        label="Final pack verification",
        quantity=Decimal("1"),
        status="pending",
        version=1,
        target_completed_at=target,
        estimate_provenance=estimate["provenance"],
        estimate_model_version=estimate["model_version"],
    )
    for task in preparation_tasks:
        await add(
            session,
            m.KitchenTaskDependency,
            task_id=packing.id,
            depends_on_task_id=task.id,
        )


async def merchant_transition(session, actor, child_id, target, version, request_id):
    candidate = await Repository(session).require(m.MerchantOrder, child_id)
    branch = await branch_scope(session, actor, candidate.branch_id)
    order = await Repository(session).require(m.Order, candidate.order_id, lock=True)
    child = await Repository(session).require(m.MerchantOrder, child_id, lock=True)
    if order.status != "confirmed":
        raise BusinessError("invalid_order", "Parent order is no longer active")
    if child.version != version:
        raise BusinessError("version_conflict", "Expected version does not match")
    if target == "ready":
        tasks_exist = await session.scalar(
            select(m.KitchenTask.id).where(m.KitchenTask.merchant_order_id == child.id).limit(1)
        )
        if not tasks_exist:
            raise BusinessError(
                "kitchen_tasks_missing",
                "Kitchen preparation tasks have not been initialized for this order",
                409,
            )
        unfinished = await session.scalar(
            select(m.KitchenTask.id)
            .where(
                m.KitchenTask.merchant_order_id == child.id,
                m.KitchenTask.status != "completed",
            )
            .limit(1)
        )
        if unfinished:
            raise BusinessError(
                "kitchen_work_incomplete",
                "Complete every preparation and packaging task before marking ready",
                409,
            )
    transition("merchant", child.status, target)
    reservations = (
        await session.scalars(
            select(m.Reservation)
            .join(m.OrderItem)
            .where(m.OrderItem.merchant_order_id == child.id)
            .order_by(m.Reservation.stock_id)
            .with_for_update(of=m.Reservation)
        )
    ).all()
    if target == "accepted":
        if any(r.status != "reserved" or r.expires_at <= now() for r in reservations):
            raise BusinessError(
                "reservation_expired", "Inventory reservation expired; order must be requoted"
            )
        for reservation in reservations:
            await session.execute(
                update(m.Stock)
                .where(m.Stock.id == reservation.stock_id)
                .values(
                    on_hand=m.Stock.on_hand - reservation.quantity,
                    reserved=m.Stock.reserved - reservation.quantity,
                    version=m.Stock.version + 1,
                )
            )
            city = await session.get(m.City, branch.city_id)
            await batches.finish(
                session,
                reservation,
                consume=True,
                at_date=now().astimezone(ZoneInfo(city.timezone)).date(),
            )
            reservation.status = "confirmed"
            await add(
                session,
                m.StockMovement,
                stock_id=reservation.stock_id,
                reservation_id=reservation.id,
                quantity=-reservation.quantity,
                kind="deduct",
                idempotency_key=f"deduct:{reservation.id}",
                actor_id=UUID(actor.subject),
            )
        await _ensure_kitchen_tasks(session, child, branch)
    if target in {"rejected", "cancelled"}:
        payment = await session.scalar(
            select(m.PaymentIntent).where(
                m.PaymentIntent.order_id == child.order_id, m.PaymentIntent.status == "confirmed"
            )
        )
        if payment:
            raise BusinessError(
                "refund_required",
                "Paid orders require an approved allocated refund before cancellation",
            )
        # Post-acceptance cancellation needs stock-return validation, not silent restocking.
        if any(r.status == "confirmed" for r in reservations):
            raise BusinessError(
                "stock_return_required",
                "Accepted inventory requires explicit return/adjustment workflow",
            )
        for reservation in reservations:
            await release_reservation(session, reservation, UUID(actor.subject), request_id)
        units = (
            await session.scalars(
                select(m.FulfillmentUnit).where(m.FulfillmentUnit.merchant_order_id == child.id)
            )
        ).all()
        for unit in units:
            unit.status = "cancelled"
            task = await session.scalar(
                select(m.DeliveryTask)
                .where(m.DeliveryTask.fulfillment_unit_id == unit.id)
                .with_for_update()
            )
            if task.status != "unassigned":
                raise BusinessError(
                    "active_delivery", "Cannot cancel a task with an active assignment"
                )
            task.status = "cancelled"
            await session.execute(
                update(m.Window)
                .where(m.Window.id == unit.window_id)
                .values(reserved=m.Window.reserved - 1)
            )
    previous = child.status
    child.status, child.version = target, child.version + 1
    await add(
        session,
        m.OrderHistory,
        order_id=child.order_id,
        merchant_order_id=child.id,
        previous=previous,
        current=target,
        actor_id=UUID(actor.subject),
    )
    await event(
        session,
        f"merchant_order.{target}",
        child.id,
        request_id,
        order_id=child.order_id,
        organization_id=branch.organization_id,
        city_id=branch.city_id,
    )
    await audit(
        session,
        actor,
        "merchant_order.transition",
        child.id,
        request_id,
        previous=previous,
        current=target,
        version=child.version,
    )
    return child


async def cancel_order(session, actor, order_id, version, request_id):
    order = await Repository(session).require(m.Order, order_id, lock=True)
    owned(actor, order.user_id)
    if order.version != version or order.status != "confirmed":
        raise BusinessError("version_conflict", "Order state or version changed")
    payments = (
        await session.scalars(
            select(m.PaymentIntent).where(m.PaymentIntent.order_id == order.id).with_for_update()
        )
    ).all()
    if any(payment.status == "confirmed" for payment in payments):
        raise BusinessError(
            "refund_required", "Paid cancellation requires approved allocated refund processing"
        )
    children = (
        await session.scalars(
            select(m.MerchantOrder)
            .where(m.MerchantOrder.order_id == order.id)
            .order_by(m.MerchantOrder.id)
            .with_for_update()
        )
    ).all()
    if any(child.status != "pending" for child in children):
        raise BusinessError(
            "merchant_processing", "Only unaccepted orders can be cancelled directly"
        )
    reservations = (
        await session.scalars(
            select(m.Reservation)
            .join(m.OrderItem)
            .join(m.MerchantOrder)
            .where(m.MerchantOrder.order_id == order.id)
            .order_by(m.Reservation.stock_id, m.Reservation.id)
            .with_for_update(of=m.Reservation)
        )
    ).all()
    for reservation in reservations:
        await release_reservation(session, reservation, UUID(actor.subject), request_id)
    units = (
        await session.scalars(
            select(m.FulfillmentUnit)
            .join(m.MerchantOrder)
            .where(m.MerchantOrder.order_id == order.id)
            .order_by(m.FulfillmentUnit.window_id, m.FulfillmentUnit.id)
            .with_for_update(of=m.FulfillmentUnit)
        )
    ).all()
    for unit in units:
        task = await session.scalar(
            select(m.DeliveryTask)
            .where(m.DeliveryTask.fulfillment_unit_id == unit.id)
            .with_for_update()
        )
        if task.status != "unassigned":
            raise BusinessError("active_delivery", "Delivery is already active")
        task.status, unit.status = "cancelled", "cancelled"
        await session.execute(
            update(m.Window)
            .where(m.Window.id == unit.window_id)
            .values(reserved=m.Window.reserved - 1)
        )
    for child in children:
        child.status, child.version = "cancelled", child.version + 1
    for payment in payments:
        payment.status = "cancelled"
    order.status, order.version = "cancelled", order.version + 1
    await add(
        session,
        m.OrderHistory,
        order_id=order.id,
        previous="confirmed",
        current="cancelled",
        actor_id=UUID(actor.subject),
    )
    await event(session, "order.cancelled", order.id, request_id)
    return order
