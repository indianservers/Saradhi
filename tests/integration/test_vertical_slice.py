import asyncio
import hmac
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import DBAPIError

from backend.application import commerce, events, maintenance
from backend.application.common import add, now
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from tests.integration.helpers import checkout, post, user, world


async def complete_kitchen_work(client, child, merchant):
    branch_id = child["branch_id"]
    headers = merchant["headers"]
    tasks_response = await client.get(
        f"/api/v1/merchant/branches/{branch_id}/kitchen/tasks?limit=100", headers=headers
    )
    assert tasks_response.status_code == 200, tasks_response.text
    tasks = tasks_response.json()["items"]
    assert tasks
    for task in sorted(tasks, key=lambda row: row["task_type"] == "packing"):
        if task["status"] == "pending":
            start = await client.post(
                f"/api/v1/merchant/kitchen/tasks/{task['id']}/transition",
                json={"target": "in_progress", "expected_version": task["version"]},
                headers=headers,
            )
            assert start.status_code == 200, start.text
            task = start.json()
        finish = await client.post(
            f"/api/v1/merchant/kitchen/tasks/{task['id']}/transition",
            json={"target": "completed", "expected_version": task["version"]},
            headers=headers,
        )
        assert finish.status_code == 200, finish.text


async def test_kitchen_dependency_capacity_and_ready_gate(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    customer_headers = state["customer"]["headers"]
    child = (
        await client.get(f"/api/v1/orders/{order['id']}/merchant-orders", headers=customer_headers)
    ).json()["items"][0]
    merchant = state["shops"][0]["merchant"]
    branch_id = state["shops"][0]["branch"]["id"]
    for version, target in ((1, "accepted"), (2, "preparing")):
        child = await post(
            client,
            f"/merchant-orders/{child['id']}/transition",
            {"target": target, "expected_version": version},
            merchant,
            200,
        )
    tasks_response = await client.get(
        f"/api/v1/merchant/branches/{branch_id}/kitchen/tasks?limit=100",
        headers=merchant["headers"],
    )
    assert tasks_response.status_code == 200, tasks_response.text
    tasks = tasks_response.json()["items"]
    prep = [task for task in tasks if task["task_type"] == "prep"]
    packing = next(task for task in tasks if task["task_type"] == "packing")
    assert prep and set(packing["blocked_by"]) == {task["id"] for task in prep}
    assert all(task["estimate_provenance"] == "deterministic_rule" for task in tasks)
    station_response = await client.get(
        f"/api/v1/merchant/branches/{branch_id}/kitchen/stations", headers=merchant["headers"]
    )
    assert station_response.status_code == 200, station_response.text
    assert {row["name"] for row in station_response.json()} == {"Main Kitchen", "Packaging"}
    grill = await client.post(
        f"/api/v1/merchant/branches/{branch_id}/kitchen/stations",
        json={"name": "Grill", "is_packaging": False, "max_concurrent": 1},
        headers=merchant["headers"],
    )
    assert grill.status_code == 201, grill.text
    reassigned = await client.put(
        f"/api/v1/merchant/kitchen/tasks/{prep[0]['id']}/station",
        json={"station_id": grill.json()["id"], "expected_version": prep[0]["version"]},
        headers=merchant["headers"],
    )
    assert reassigned.status_code == 200, reassigned.text
    assert reassigned.json()["station_name"] == "Grill"
    prep[0] = reassigned.json()
    blocked = await client.post(
        f"/api/v1/merchant/kitchen/tasks/{packing['id']}/transition",
        json={"target": "in_progress", "expected_version": packing["version"]},
        headers=merchant["headers"],
    )
    assert blocked.status_code == 409
    _, _, second_order, _ = await checkout(client, state["customer"], state["shops"])
    second_child = (
        await client.get(
            f"/api/v1/orders/{second_order['id']}/merchant-orders", headers=customer_headers
        )
    ).json()["items"][0]
    for version, target in ((1, "accepted"), (2, "preparing")):
        second_child = await post(
            client,
            f"/merchant-orders/{second_child['id']}/transition",
            {"target": target, "expected_version": version},
            merchant,
            200,
        )
    second_tasks = (
        await client.get(
            f"/api/v1/merchant/branches/{branch_id}/kitchen/tasks?limit=100",
            headers=merchant["headers"],
        )
    ).json()["items"]
    second_prep = next(
        task
        for task in second_tasks
        if task["merchant_order_id"] == second_child["id"] and task["task_type"] == "prep"
    )
    second_assignment = await client.put(
        f"/api/v1/merchant/kitchen/tasks/{second_prep['id']}/station",
        json={"station_id": grill.json()["id"], "expected_version": second_prep["version"]},
        headers=merchant["headers"],
    )
    assert second_assignment.status_code == 200, second_assignment.text
    first_start = await client.post(
        f"/api/v1/merchant/kitchen/tasks/{prep[0]['id']}/transition",
        json={"target": "in_progress", "expected_version": prep[0]["version"]},
        headers=merchant["headers"],
    )
    assert first_start.status_code == 200, first_start.text
    at_capacity = await client.post(
        f"/api/v1/merchant/kitchen/tasks/{second_prep['id']}/transition",
        json={"target": "in_progress", "expected_version": second_assignment.json()["version"]},
        headers=merchant["headers"],
    )
    assert at_capacity.status_code == 409
    assert at_capacity.json()["error"]["code"] == "station_at_capacity"
    first_done = await client.post(
        f"/api/v1/merchant/kitchen/tasks/{prep[0]['id']}/transition",
        json={"target": "completed", "expected_version": first_start.json()["version"]},
        headers=merchant["headers"],
    )
    assert first_done.status_code == 200, first_done.text
    prep[0] = first_done.json()
    second_start = await client.post(
        f"/api/v1/merchant/kitchen/tasks/{second_prep['id']}/transition",
        json={"target": "in_progress", "expected_version": second_assignment.json()["version"]},
        headers=merchant["headers"],
    )
    assert second_start.status_code == 200, second_start.text
    second_done = await client.post(
        f"/api/v1/merchant/kitchen/tasks/{second_prep['id']}/transition",
        json={"target": "completed", "expected_version": second_start.json()["version"]},
        headers=merchant["headers"],
    )
    assert second_done.status_code == 200, second_done.text
    premature = await client.post(
        f"/api/v1/merchant-orders/{child['id']}/transition",
        json={"target": "ready", "expected_version": child["version"]},
        headers=merchant["headers"],
    )
    assert premature.status_code == 409
    for task in prep:
        if task["status"] == "completed":
            continue
        start = await client.post(
            f"/api/v1/merchant/kitchen/tasks/{task['id']}/transition",
            json={"target": "in_progress", "expected_version": task["version"]},
            headers=merchant["headers"],
        )
        assert start.status_code == 200, start.text
        done = await client.post(
            f"/api/v1/merchant/kitchen/tasks/{task['id']}/transition",
            json={"target": "completed", "expected_version": start.json()["version"]},
            headers=merchant["headers"],
        )
        assert done.status_code == 200, done.text
    packing_start = await client.post(
        f"/api/v1/merchant/kitchen/tasks/{packing['id']}/transition",
        json={"target": "in_progress", "expected_version": packing["version"]},
        headers=merchant["headers"],
    )
    assert packing_start.status_code == 200, packing_start.text
    packing_done = await client.post(
        f"/api/v1/merchant/kitchen/tasks/{packing['id']}/transition",
        json={"target": "completed", "expected_version": packing_start.json()["version"]},
        headers=merchant["headers"],
    )
    assert packing_done.status_code == 200, packing_done.text
    ready = await client.post(
        f"/api/v1/merchant-orders/{child['id']}/transition",
        json={"target": "ready", "expected_version": child["version"]},
        headers=merchant["headers"],
    )
    assert ready.status_code == 200 and ready.json()["status"] == "ready"


async def test_customer_identity_rotation_and_logout(api):
    client, app = api
    identity = await user(client, app)
    duplicate = await client.post(
        "/api/v1/auth/register", json={"email": identity["email"], "password": identity["password"]}
    )
    assert duplicate.status_code == 409
    invalid = await client.post(
        "/api/v1/auth/login", json={"email": identity["email"], "password": "incorrect-password"}
    )
    assert invalid.status_code == 401
    invalid_token = await client.get("/api/v1/me", headers={"Authorization": "Bearer invalid"})
    assert invalid_token.status_code == 401
    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": identity["tokens"]["refresh_token"]}
    )
    assert refreshed.status_code == 200
    replay = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": identity["tokens"]["refresh_token"]}
    )
    assert replay.status_code == 401
    revoked = await client.get(
        "/api/v1/me", headers={"Authorization": "Bearer " + refreshed.json()["access_token"]}
    )
    assert revoked.status_code == 401
    login = await client.post(
        "/api/v1/auth/login", json={"email": identity["email"], "password": identity["password"]}
    )
    logged_out = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login.json()["refresh_token"]},
        headers={"Authorization": "Bearer " + login.json()["access_token"]},
    )
    assert logged_out.status_code == 204
    assert (
        await client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + login.json()["access_token"]}
        )
    ).status_code == 401


async def test_cross_organization_and_admin_denial(api):
    client, app = api
    state = await world(client, app)
    first, second = state["shops"]
    foreign = await client.post(
        f"/api/v1/merchants/branches/{second['branch']['id']}/hours",
        json={"weekday": 0, "opens_at": "09:00", "closes_at": "10:00"},
        headers=first["merchant"]["headers"],
    )
    assert foreign.status_code == 403
    unauthorized = await client.post(
        "/api/v1/geo/countries",
        json={"name": "Denied", "code": "XY"},
        headers=state["customer"]["headers"],
    )
    assert unauthorized.status_code == 403
    foreign_stock = await client.get(
        f"/api/v1/inventory/branches/{second['branch']['id']}", headers=first["merchant"]["headers"]
    )
    assert foreign_stock.status_code == 403


async def test_city_dispatch_snapshot_and_versioned_scoring_policy(api):
    client, app = api
    state = await world(client, app, 1)
    city_id = state["city"]["id"]
    first = await client.put(
        f"/api/v1/operations/cities/{city_id}/dispatch-policy",
        json={"weights": {"pickup_distance": "1", "workload": "5"}},
        headers=state["admin"]["headers"],
    )
    second = await client.put(
        f"/api/v1/operations/cities/{city_id}/dispatch-policy",
        json={"weights": {"pickup_distance": "2", "workload": "8"}},
        headers=state["admin"]["headers"],
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["version"] == 1 and second.json()["version"] == 2
    dispatch = await client.get(
        f"/api/v1/operations/cities/{city_id}/dispatch", headers=state["admin"]["headers"]
    )
    fleet = await client.get(
        f"/api/v1/operations/cities/{city_id}/fleet", headers=state["admin"]["headers"]
    )
    assert dispatch.status_code == fleet.status_code == 200
    denied = await client.get(
        f"/api/v1/operations/cities/{city_id}/dispatch",
        headers=state["customer"]["headers"],
    )
    assert denied.status_code == 403
    city_manager = await user(client, app)
    async with app.state.sessions.begin() as db:
        role = await db.scalar(select(m.Role).where(m.Role.name == "city_manager"))
        await add(
            db,
            m.RoleAssignment,
            user_id=UUID(city_manager["id"]),
            role_id=role.id,
            organization_id=UUID(state["shops"][0]["organization"]["id"]),
            city_id=UUID(city_id),
            branch_id=None,
        )
    authorized = await client.get(
        f"/api/v1/operations/cities/{city_id}/fleet",
        headers=city_manager["headers"],
    )
    outside = await client.get(
        f"/api/v1/operations/cities/{uuid4()}/fleet",
        headers=city_manager["headers"],
    )
    assert authorized.status_code == 200 and outside.status_code == 403


async def test_multimerchant_multislot_checkout_and_idempotency(api):
    client, app = api
    state = await world(client, app)
    cart, quote, order, key = await checkout(client, state["customer"], state["shops"])
    assert Decimal(order["total"]) == Decimal("20")
    repeated = await post(
        client,
        "/orders/confirm",
        {"quote_id": quote["id"]},
        state["customer"],
        headers={"Idempotency-Key": key},
    )
    assert repeated["id"] == order["id"]
    children = await client.get(
        f"/api/v1/orders/{order['id']}/merchant-orders", headers=state["customer"]["headers"]
    )
    assert len(children.json()["items"]) == 2
    assert len({child["branch_id"] for child in children.json()["items"]}) == 2
    async with app.state.sessions() as db:
        units = (
            await db.scalars(
                select(m.FulfillmentUnit)
                .join(m.MerchantOrder)
                .where(m.MerchantOrder.order_id == UUID(order["id"]))
            )
        ).all()
        assert len(units) == 2 and len({unit.window_id for unit in units}) == 2
        assert (
            await db.scalar(
                select(func.count())
                .select_from(m.Order)
                .where(m.Order.quote_id == UUID(quote["id"]))
            )
            == 1
        )
        outbox = (
            await db.scalars(
                select(m.Outbox.event_type).where(m.Outbox.aggregate_id == UUID(order["id"]))
            )
        ).all()
        assert {"order.created", "order.confirmed"} <= set(outbox)
        reserved = (
            await db.scalars(
                select(m.Reservation)
                .join(m.OrderItem)
                .join(m.MerchantOrder)
                .where(m.MerchantOrder.order_id == UUID(order["id"]))
            )
        ).all()
        assert len(reserved) == 2
    denied = await client.get(
        f"/api/v1/orders/{order['id']}", headers=state["shops"][0]["merchant"]["headers"]
    )
    assert denied.status_code == 403


async def test_customer_catalog_cart_reload_and_quote_lines(api):
    client, app = api
    state = await world(client, app, 1)
    customer = state["customer"]
    branch = state["shops"][0]["branch"]

    discovery = await client.get(
        "/api/v1/merchants/branches", params={"city_id": state["city"]["id"]}
    )
    assert discovery.status_code == 200
    assert discovery.json()["items"][0]["merchant_type"] == "food"

    catalog = await client.get(
        "/api/v1/catalog/products",
        params={"branch_id": branch["id"], "q": "Integration product"},
        headers=customer["headers"],
    )
    assert catalog.status_code == 200
    product = catalog.json()["items"][0]
    assert product["name"] == "Integration product"
    assert product["unit_price"] == "10.0000"
    assert product["available_quantity"] == "10.0000"

    cart = await post(client, "/carts", None, customer)
    for shop in state["shops"]:
        await post(
            client,
            f"/carts/{cart['id']}/items",
            {
                "branch_id": shop["branch"]["id"],
                "variant_id": shop["variant"]["id"],
                "quantity": "1",
                "window_id": shop["window"]["id"],
            },
            customer,
        )
    reloaded = await client.get(f"/api/v1/carts/{cart['id']}", headers=customer["headers"])
    lines = await client.get(f"/api/v1/carts/{cart['id']}/items", headers=customer["headers"])
    assert reloaded.status_code == 200
    assert reloaded.json()["version"] == 2
    assert len(lines.json()["items"]) == 1
    quote = await post(client, f"/carts/{cart['id']}/quote", None, customer)
    assert quote["total"] == "10.00"
    assert quote["lines"][0]["product_name"] == "Integration product"
    assert quote["lines"][0]["unit_price"] == "10.0000"
    assert quote["lines"][0]["branch_name"] == "Integration branch"
    assert quote["lines"][0]["window_starts_at"]
    order = await post(
        client,
        "/orders/confirm",
        {"quote_id": quote["id"]},
        customer,
        headers={"Idempotency-Key": uuid4().hex},
    )
    intent = await client.post(
        "/api/v1/finance/sandbox/payment-intents",
        json={"order_id": order["id"]},
        headers=customer["headers"],
    )
    assert intent.status_code == 201 and intent.json()["status"] == "pending"
    completed = await client.post(
        f"/api/v1/finance/sandbox/payments/{intent.json()['id']}/complete",
        headers=customer["headers"],
    )
    assert completed.status_code == 200 and completed.json()["status"] == "confirmed"
    payment_status = await client.get(
        f"/api/v1/orders/{order['id']}/payment", headers=customer["headers"]
    )
    assert payment_status.status_code == 200 and payment_status.json()["id"] == intent.json()["id"]
    reorder = await client.get(
        f"/api/v1/orders/{order['id']}/reorder-lines", headers=customer["headers"]
    )
    assert reorder.status_code == 200
    assert reorder.json()[0]["variant_id"] == state["shops"][0]["variant"]["id"]

    other_customer = await user(client, app)
    denied_cart = await client.get(f"/api/v1/carts/{cart['id']}", headers=other_customer["headers"])
    assert denied_cart.status_code == 403
    denied_payment = await client.post(
        f"/api/v1/finance/sandbox/payments/{intent.json()['id']}/complete",
        headers=other_customer["headers"],
    )
    assert denied_payment.status_code == 403
    denied_order_payment = await client.get(
        f"/api/v1/orders/{order['id']}/payment", headers=other_customer["headers"]
    )
    assert denied_order_payment.status_code == 403
    denied_reorder = await client.get(
        f"/api/v1/orders/{order['id']}/reorder-lines", headers=other_customer["headers"]
    )
    assert denied_reorder.status_code == 403


async def test_merchant_workspace_branch_scope_queue_and_transitions(api):
    client, app = api
    state = await world(client, app, 2)
    customer = state["customer"]
    merchant_a, merchant_b = state["shops"]
    _, _, order, _ = await checkout(client, customer, [merchant_a])
    customer_children = await client.get(
        f"/api/v1/orders/{order['id']}/merchant-orders", headers=customer["headers"]
    )
    child_id = customer_children.json()["items"][0]["id"]

    branches = await client.get(
        "/api/v1/merchant/branches", headers=merchant_a["merchant"]["headers"]
    )
    assert branches.status_code == 200
    assert [row["id"] for row in branches.json()["items"]] == [merchant_a["branch"]["id"]]
    current_branch = branches.json()["items"][0]
    paused = await client.put(
        f"/api/v1/merchant/branches/{merchant_a['branch']['id']}/availability",
        json={"accepting_orders": False, "expected_version": current_branch["version"]},
        headers=merchant_a["merchant"]["headers"],
    )
    assert paused.status_code == 200 and paused.json()["accepting_orders"] is False
    stale_availability = await client.put(
        f"/api/v1/merchant/branches/{merchant_a['branch']['id']}/availability",
        json={"accepting_orders": True, "expected_version": current_branch["version"]},
        headers=merchant_a["merchant"]["headers"],
    )
    assert stale_availability.status_code == 409
    queue = await client.get(
        f"/api/v1/merchant/branches/{merchant_a['branch']['id']}/orders",
        headers=merchant_a["merchant"]["headers"],
    )
    assert queue.status_code == 200
    assert len(queue.json()["items"]) == 1
    assert queue.json()["items"][0]["id"] == child_id
    assert queue.json()["items"][0]["items"][0]["product_name"] == "Integration product"
    foreign_queue = await client.get(
        f"/api/v1/merchant/branches/{merchant_b['branch']['id']}/orders",
        headers=merchant_a["merchant"]["headers"],
    )
    assert foreign_queue.status_code == 403

    catalog = await client.get(
        f"/api/v1/merchant/branches/{merchant_a['branch']['id']}/catalog",
        headers=merchant_a["merchant"]["headers"],
    )
    assert catalog.status_code == 200
    assert catalog.json()["items"][0]["name"] == "Integration product"
    assert catalog.json()["items"][0]["on_hand"] == "10.0000"
    denied_catalog = await client.get(
        f"/api/v1/merchant/branches/{merchant_b['branch']['id']}/catalog",
        headers=merchant_a["merchant"]["headers"],
    )
    assert denied_catalog.status_code == 403

    accepted = await client.post(
        f"/api/v1/merchant-orders/{child_id}/transition",
        json={"target": "accepted", "expected_version": 1},
        headers=merchant_a["merchant"]["headers"],
    )
    assert accepted.status_code == 200 and accepted.json()["status"] == "accepted"
    stale = await client.post(
        f"/api/v1/merchant-orders/{child_id}/transition",
        json={"target": "preparing", "expected_version": 1},
        headers=merchant_a["merchant"]["headers"],
    )
    assert stale.status_code == 409

    onboarding = await client.post(
        "/api/v1/merchant/onboarding",
        json={
            "organization_name": "Atomic onboarding merchant",
            "brand_name": "Atomic onboarding brand",
            "merchant_type": "food",
            "branch_name": "Atomic onboarding branch",
            "city_id": state["city"]["id"],
            "latitude": "17.385",
            "longitude": "78.4867",
        },
        headers=merchant_b["merchant"]["headers"],
    )
    assert onboarding.status_code == 201
    assert onboarding.json()["status"] == "pending"
    assert onboarding.json()["accepting_orders"] is False
    own_after_onboarding = await client.get(
        "/api/v1/merchant/branches", headers=merchant_b["merchant"]["headers"]
    )
    assert onboarding.json()["id"] in {row["id"] for row in own_after_onboarding.json()["items"]}


async def test_rejected_child_blocks_parent_sandbox_payment(api):
    client, app = api
    state = await world(client, app, 2)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    children = (
        await client.get(
            f"/api/v1/orders/{order['id']}/merchant-orders",
            headers=state["customer"]["headers"],
        )
    ).json()["items"]
    rejected = await post(
        client,
        f"/merchant-orders/{children[0]['id']}/transition",
        {"target": "rejected", "expected_version": 1},
        state["admin"],
        200,
    )
    assert rejected["status"] == "rejected"
    assert children[1]["status"] == "pending"
    payment = await client.post(
        "/api/v1/finance/sandbox/payment-intents",
        json={"order_id": order["id"]},
        headers=state["customer"]["headers"],
    )
    assert payment.status_code == 409
    assert payment.json()["error"]["code"] == "revised_payment_required"
    async with app.state.sessions() as db:
        refreshed = (
            await db.scalars(
                select(m.MerchantOrder)
                .where(m.MerchantOrder.order_id == UUID(order["id"]))
                .order_by(m.MerchantOrder.id)
            )
        ).all()
        assert {row.status for row in refreshed} == {"rejected", "pending"}
        assert (
            await db.scalar(
                select(func.count())
                .select_from(m.PaymentIntent)
                .where(m.PaymentIntent.order_id == UUID(order["id"]))
            )
            == 0
        )


async def test_branch_hours_and_unserviceable_destination(api):
    client, app = api
    state = await world(client, app, 1)
    shop = state["shops"][0]
    address = await post(
        client,
        "/addresses",
        {
            "city_id": state["city"]["id"],
            "label": "Test",
            "address_text": "Test-only destination",
            "latitude": "17.5",
            "longitude": "78.5",
        },
        state["customer"],
    )
    cart = await post(client, "/carts", None, state["customer"])
    await post(
        client,
        f"/carts/{cart['id']}/items",
        {
            "branch_id": shop["branch"]["id"],
            "variant_id": shop["variant"]["id"],
            "quantity": "1",
            "window_id": shop["window"]["id"],
            "address_id": address["id"],
            "delivery_method": "courier",
        },
        state["customer"],
    )
    response = await client.post(
        f"/api/v1/carts/{cart['id']}/quote", headers=state["customer"]["headers"]
    )
    assert (
        response.status_code == 409
    )  # No courier capability, never silently assume citywide service.
    await post(
        client,
        f"/merchants/branches/{shop['branch']['id']}/capabilities",
        {"method": "courier"},
        shop["merchant"],
    )
    response = await client.post(
        f"/api/v1/carts/{cart['id']}/quote", headers=state["customer"]["headers"]
    )
    assert response.status_code in {
        409,
        503,
    }  # No configured spatial area, or explicit PostGIS blocker.
    async with app.state.sessions.begin() as db:
        await db.execute(
            update(m.OperatingHour)
            .where(m.OperatingHour.branch_id == UUID(shop["branch"]["id"]))
            .values(
                opens_at=__import__("datetime").time(20), closes_at=__import__("datetime").time(21)
            )
        )
    pickup_cart = await post(client, "/carts", None, state["customer"])
    await post(
        client,
        f"/carts/{pickup_cart['id']}/items",
        {
            "branch_id": shop["branch"]["id"],
            "variant_id": shop["variant"]["id"],
            "quantity": "1",
            "window_id": shop["window"]["id"],
        },
        state["customer"],
    )
    closed = await client.post(
        f"/api/v1/carts/{pickup_cart['id']}/quote", headers=state["customer"]["headers"]
    )
    assert closed.status_code == 409 and closed.json()["error"]["code"] == "merchant_closed"


async def test_atomic_last_unit_concurrent_checkout(api):
    client, app = api
    state = await world(client, app, 1)
    shop = state["shops"][0]
    await post(
        client,
        f"/inventory/branches/{shop['branch']['id']}/adjustments",
        {"variant_id": shop["variant"]["id"], "delta": "-9", "idempotency_key": uuid4().hex},
        shop["merchant"],
        200,
    )
    quotes = []
    for _ in range(2):
        cart = await post(client, "/carts", None, state["customer"])
        await post(
            client,
            f"/carts/{cart['id']}/items",
            {
                "branch_id": shop["branch"]["id"],
                "variant_id": shop["variant"]["id"],
                "quantity": "1",
                "window_id": shop["window"]["id"],
            },
            state["customer"],
        )
        quotes.append(await post(client, f"/carts/{cart['id']}/quote", None, state["customer"]))

    async def place(quote):
        return await client.post(
            "/api/v1/orders/confirm",
            json={"quote_id": quote["id"]},
            headers={**state["customer"]["headers"], "Idempotency-Key": uuid4().hex},
        )

    results = await asyncio.gather(*(place(quote) for quote in quotes))
    assert sorted(response.status_code for response in results) == [201, 409]
    async with app.state.sessions() as db:
        stock = await db.get(m.Stock, UUID(shop["stock"]["id"]))
        assert stock.on_hand == 1 and stock.reserved == 1


async def test_release_and_expiration_are_idempotent(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    async with app.state.sessions.begin() as db:
        reservation = await db.scalar(
            select(m.Reservation)
            .join(m.OrderItem)
            .join(m.MerchantOrder)
            .where(m.MerchantOrder.order_id == UUID(order["id"]))
            .with_for_update(of=m.Reservation)
        )
        rid = reservation.id
        reservation.expires_at = now() - timedelta(seconds=1)
    async with app.state.sessions.begin() as db:
        assert await maintenance.expire_reservations(db, reservation_id=rid) == 1
    async with app.state.sessions.begin() as db:
        row = await db.get(m.Reservation, rid)
        await commerce.release_reservation(db, row, None, "test-repeat")
        assert row.status == "released"
    async with app.state.sessions() as db:
        stock = await db.get(m.Stock, UUID(state["shops"][0]["stock"]["id"]))
        assert stock.reserved == 0
        assert (
            await db.scalar(
                select(func.count())
                .select_from(m.StockMovement)
                .where(m.StockMovement.idempotency_key == f"release:{rid}")
            )
            == 1
        )


async def test_merchant_transition_and_recipient_pickup(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    children = await client.get(
        f"/api/v1/orders/{order['id']}/merchant-orders", headers=state["customer"]["headers"]
    )
    child = children.json()["items"][0]
    denied = await client.post(
        f"/api/v1/merchant-orders/{child['id']}/transition",
        json={"target": "ready", "expected_version": 1},
        headers=state["customer"]["headers"],
    )
    assert denied.status_code == 403
    invalid = await client.post(
        f"/api/v1/merchant-orders/{child['id']}/transition",
        json={"target": "ready", "expected_version": 1},
        headers=state["shops"][0]["merchant"]["headers"],
    )
    assert invalid.status_code == 409
    for version, target in enumerate(["accepted", "preparing"], start=1):
        child = await post(
            client,
            f"/merchant-orders/{child['id']}/transition",
            {"target": target, "expected_version": version},
            state["shops"][0]["merchant"],
            200,
        )
    await complete_kitchen_work(client, child, state["shops"][0]["merchant"])
    child = await post(
        client,
        f"/merchant-orders/{child['id']}/transition",
        {"target": "ready", "expected_version": child["version"]},
        state["shops"][0]["merchant"],
        200,
    )
    async with app.state.sessions() as db:
        task = await db.scalar(
            select(m.DeliveryTask)
            .join(m.FulfillmentUnit)
            .where(m.FulfillmentUnit.merchant_order_id == UUID(child["id"]))
        )
        task_id = str(task.id)
    unauthorized = await client.post(
        f"/api/v1/delivery-tasks/{task_id}/acknowledge",
        json={"expected_version": 1},
        headers=state["shops"][0]["merchant"]["headers"],
    )
    assert unauthorized.status_code == 403
    delivered = await post(
        client,
        f"/delivery-tasks/{task_id}/acknowledge",
        {"expected_version": 1},
        state["customer"],
        200,
    )
    assert delivered["status"] == "delivered"
    final = await client.get(f"/api/v1/orders/{order['id']}", headers=state["customer"]["headers"])
    assert final.json()["status"] == "completed"


async def test_pilot_exclusive_accept_pickup_and_completion(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    async with app.state.sessions.begin() as db:
        child = await db.scalar(
            select(m.MerchantOrder).where(m.MerchantOrder.order_id == UUID(order["id"]))
        )
        unit = await db.scalar(
            select(m.FulfillmentUnit).where(m.FulfillmentUnit.merchant_order_id == child.id)
        )
        # Explicit logistics fixture: serviceability is tested separately; this is not a
        # fabricated production coverage polygon or a bypass exposed by any API.
        unit.delivery_method = "courier"
        unit.address_snapshot = {
            "address_text": "Integration recipient address",
            "latitude": "17.3800000",
            "longitude": "78.4800000",
        }
        task = await db.scalar(
            select(m.DeliveryTask).where(m.DeliveryTask.fulfillment_unit_id == unit.id)
        )
        child_id, task_id = str(child.id), str(task.id)
    for version, target in enumerate(["accepted", "preparing"], 1):
        await post(
            client,
            f"/merchant-orders/{child_id}/transition",
            {"target": target, "expected_version": version},
            state["shops"][0]["merchant"],
            200,
        )
    child_payload = {"id": child_id, "branch_id": state["shops"][0]["branch"]["id"]}
    await complete_kitchen_work(client, child_payload, state["shops"][0]["merchant"])
    await post(
        client,
        f"/merchant-orders/{child_id}/transition",
        {"target": "ready", "expected_version": 3},
        state["shops"][0]["merchant"],
        200,
    )
    identities = [await user(client, app), await user(client, app)]
    pilots = []
    for identity in identities:
        pilot = await post(client, "/pilots", {"city_id": state["city"]["id"]}, identity)
        await post(client, f"/pilots/{pilot['id']}/verify", None, state["admin"], 200)
        consent = await client.post(
            "/api/v1/pilots/me/location-consent",
            json={"accepted": True, "policy_version": "pilot-location-v1"},
            headers=identity["headers"],
        )
        assert consent.status_code == 200
        location = await client.post(
            "/api/v1/pilots/me/location",
            json={
                "latitude": "17.385",
                "longitude": "78.4867",
                "observed_at": now().isoformat(),
                "accuracy_m": "8",
                "client_sequence": 1,
                "app_state": "foreground",
            },
            headers=identity["headers"],
        )
        assert location.status_code == 200 and location.json()["accepted"]
        available = await client.put(
            f"/api/v1/pilots/{pilot['id']}/availability",
            json={"available": True},
            headers=identity["headers"],
        )
        assert available.status_code == 200
        pilots.append(pilot)

    ai_dispatch_started = perf_counter()
    recommendation = await client.post(
        "/api/v1/ai/dispatch/optimize",
        json={"city_id": state["city"]["id"], "task_ids": [task_id]},
        headers=state["admin"]["headers"],
    )
    ai_dispatch_api_ms = round((perf_counter() - ai_dispatch_started) * 1000, 2)
    assert recommendation.status_code == 200
    assert recommendation.json()["committed"] is False
    assert len(recommendation.json()["plan"]) == 1
    assert recommendation.json()["constraint_checks"]["pilot_capacity"] is True
    Path("docs/ai/dispatch-optimization-smoke.json").write_text(
        json.dumps(
            {
                "scope": "local ASGI + PostgreSQL, one task/two pilot candidates",
                "api_latency_ms": ai_dispatch_api_ms,
                "algorithm_runtime_ms": recommendation.json()["runtime_ms"],
                "plan_size": len(recommendation.json()["plan"]),
                "committed": False,
                "limitations": "single scenario; not a solver or fleet-scale benchmark",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    async def offer(pilot):
        return await client.post(
            f"/api/v1/delivery-tasks/{task_id}/offer",
            json={"pilot_id": pilot["id"]},
            headers=state["shops"][0]["merchant"]["headers"],
        )

    dispatch_started = perf_counter()
    responses = await asyncio.gather(*(offer(pilot) for pilot in pilots))
    dispatch_latency_ms = round((perf_counter() - dispatch_started) * 1000, 2)
    assert sorted(response.status_code for response in responses) == [201, 409]
    Path("docs/performance/dispatch-offer-smoke.json").write_text(
        json.dumps(
            {
                "scope": "local ASGI API + PostgreSQL, two concurrent pilot offer requests",
                "concurrent_requests": len(responses),
                "winner_and_conflict_latency_ms": dispatch_latency_ms,
                "limitations": (
                    "single task, two candidates, local test harness; not fleet-scale latency"
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    winner = next(i for i, r in enumerate(responses) if r.status_code == 201)
    assignment = responses[winner].json()
    pilot_profile = await client.get("/api/v1/pilots/me", headers=identities[winner]["headers"])
    assert pilot_profile.status_code == 200 and pilot_profile.json()["verified"] is True
    own_work = await client.get(
        "/api/v1/pilots/me/assignments", headers=identities[winner]["headers"]
    )
    assert own_work.status_code == 200
    offered_task = next(
        row for row in own_work.json()["items"] if row["assignment_status"] == "offered"
    )
    assert offered_task["delivery_task_id"] == task_id and offered_task["dropoff"] is None
    cannot_go_offline = await client.put(
        f"/api/v1/pilots/{pilots[winner]['id']}/availability",
        json={"available": False},
        headers=identities[winner]["headers"],
    )
    assert cannot_go_offline.status_code == 409
    cannot_go_offline_v2 = await client.post(
        "/api/v1/pilots/me/availability",
        json={"state": "offline"},
        headers=identities[winner]["headers"],
    )
    assert cannot_go_offline_v2.status_code == 409
    cannot_break = await client.post(
        "/api/v1/pilots/me/availability",
        json={"state": "on_break"},
        headers=identities[winner]["headers"],
    )
    assert cannot_break.status_code == 409
    other_work = await client.get(
        "/api/v1/pilots/me/assignments", headers=identities[1 - winner]["headers"]
    )
    assert other_work.status_code == 200 and other_work.json()["items"] == []
    wrong = await client.post(
        f"/api/v1/pilot-assignments/{assignment['id']}/accept",
        headers=identities[1 - winner]["headers"],
    )
    assert wrong.status_code == 403
    async with app.state.sessions.begin() as db:
        pilot_row = await db.get(m.Pilot, UUID(pilots[winner]["id"]))
        previous_state = pilot_row.state
        pilot_row.state = "offline"
    unavailable_accept = await client.post(
        f"/api/v1/pilot-assignments/{assignment['id']}/accept",
        headers=identities[winner]["headers"],
    )
    assert unavailable_accept.status_code == 409
    async with app.state.sessions.begin() as db:
        pilot_row = await db.get(m.Pilot, UUID(pilots[winner]["id"]))
        pilot_row.state = previous_state
    accepted = await post(
        client, f"/pilot-assignments/{assignment['id']}/accept", None, identities[winner], 200
    )
    cannot_break_with_active_task = await client.post(
        "/api/v1/pilots/me/availability",
        json={"state": "on_break"},
        headers=identities[winner]["headers"],
    )
    assert cannot_break_with_active_task.status_code == 409
    accepted_work = await client.get(
        "/api/v1/pilots/me/assignments", headers=identities[winner]["headers"]
    )
    accepted_task = next(
        row for row in accepted_work.json()["items"] if row["delivery_task_id"] == task_id
    )
    assert accepted_task["dropoff"] is not None
    earnings = await client.get("/api/v1/pilots/me/earnings", headers=identities[winner]["headers"])
    assert earnings.status_code == 200 and earnings.json()["items"] == []
    picked = await post(
        client,
        f"/delivery-tasks/{task_id}/pickup",
        {"expected_version": accepted["version"]},
        identities[winner],
        200,
    )
    assert picked["status"] == "picked_up"
    delivery_issue = await client.post(
        "/api/v1/pilots/me/incidents",
        json={
            "category": "low_battery",
            "summary": "The phone battery is too low to finish this delivery.",
            "delivery_task_id": task_id,
        },
        headers=identities[winner]["headers"],
    )
    assert delivery_issue.status_code == 201, delivery_issue.text
    assert delivery_issue.json()["severity"] == "normal"
    stolen_issue = await client.post(
        "/api/v1/pilots/me/incidents",
        json={
            "category": "low_battery",
            "summary": "The phone battery is too low to finish this delivery.",
            "delivery_task_id": task_id,
        },
        headers=identities[1 - winner]["headers"],
    )
    assert stolen_issue.status_code == 403
    delivered = await post(
        client,
        f"/delivery-tasks/{task_id}/acknowledge",
        {"expected_version": picked["version"]},
        state["customer"],
        200,
    )
    assert delivered["status"] == "delivered"


async def test_pilot_operations_and_advisory_are_self_and_zone_scoped(api):
    client, app = api
    state = await world(client, app, 1)
    identities = [await user(client, app), await user(client, app)]
    pilots = [
        await post(client, "/pilots", {"city_id": state["city"]["id"]}, identity)
        for identity in identities
    ]
    Shift = F["fulfillment.pilot_shifts"]
    PilotZone = F["fulfillment.pilot_service_zones"]
    Capability = F["fulfillment.pilot_capabilities"]
    instant = now()
    async with app.state.sessions.begin() as db:
        zone = await add(
            db,
            m.Zone,
            city_id=UUID(state["city"]["id"]),
            name=f"Pilot zone {uuid4().hex[:8]}",
            active=True,
        )
        await add(
            db,
            PilotZone,
            pilot_id=UUID(pilots[0]["id"]),
            zone_id=zone.id,
        )
        await add(
            db,
            Shift,
            pilot_id=UUID(pilots[0]["id"]),
            starts_at=instant - timedelta(minutes=30),
            ends_at=instant + timedelta(minutes=90),
        )
        await add(
            db,
            Capability,
            pilot_id=UUID(pilots[0]["id"]),
            capability="insulated_bag",
            expires_at=instant + timedelta(days=30),
        )

    own_operations = await client.get(
        "/api/v1/pilots/me/operations", headers=identities[0]["headers"]
    )
    assert own_operations.status_code == 200, own_operations.text
    own = own_operations.json()
    assert own["shift"]["status"] == "active"
    assert 89 <= own["shift"]["remaining_minutes"] <= 90
    assert own["capabilities"] == ["insulated_bag"]
    assert own["authorized_zones"] == [{"id": str(zone.id), "name": zone.name}]

    other_operations = await client.get(
        "/api/v1/pilots/me/operations", headers=identities[1]["headers"]
    )
    assert other_operations.status_code == 200
    assert other_operations.json()["shift"] is None
    assert other_operations.json()["authorized_zones"] == []
    assert other_operations.json()["capabilities"] == []

    outlook = await client.get("/api/v1/pilots/me/supply-demand", headers=identities[0]["headers"])
    assert outlook.status_code == 200, outlook.text
    payload = outlook.json()
    assert payload["advisory_only"] is True
    assert payload["pilot_supply"] == "zone_level_supply_unavailable"
    assert len(payload["signals"]) == 1
    signal = payload["signals"][0]
    assert signal["zone_id"] == str(zone.id)
    assert signal["signal_type"] == "prediction"
    assert signal["demand_band"] in {"low", "moderate", "high", "insufficient_history"}
    assert "horizons" not in signal and "sample_count" not in signal
    other_outlook = await client.get(
        "/api/v1/pilots/me/supply-demand", headers=identities[1]["headers"]
    )
    assert other_outlook.status_code == 200
    assert other_outlook.json()["signals"] == []

    await post(client, f"/pilots/{pilots[0]['id']}/verify", None, state["admin"], 200)
    consent = await client.post(
        "/api/v1/pilots/me/location-consent",
        json={"accepted": True, "policy_version": "pilot-location-v1"},
        headers=identities[0]["headers"],
    )
    assert consent.status_code == 200
    location = await client.post(
        "/api/v1/pilots/me/location",
        json={
            "latitude": "17.385",
            "longitude": "78.4867",
            "observed_at": now().isoformat(),
            "accuracy_m": "8",
            "client_sequence": 1,
            "app_state": "foreground",
        },
        headers=identities[0]["headers"],
    )
    assert location.status_code == 200 and location.json()["accepted"]
    reported = await client.post(
        "/api/v1/pilots/me/incidents",
        json={
            "category": "accident",
            "summary": "Pilot reported an accident during a test delivery.",
            "safety_emergency": False,
        },
        headers=identities[0]["headers"],
    )
    assert reported.status_code == 201, reported.text
    incident = reported.json()
    assert incident["severity"] == "critical" and incident["safety_emergency"] is True
    assert "emergency services" in incident["next_step"]
    profile = await client.get("/api/v1/pilots/me", headers=identities[0]["headers"])
    assert profile.status_code == 200 and profile.json()["state"] == "unavailable"
    cannot_resume = await client.post(
        "/api/v1/pilots/me/availability",
        json={"state": "online_available"},
        headers=identities[0]["headers"],
    )
    assert cannot_resume.status_code == 409
    own_incidents = await client.get(
        "/api/v1/pilots/me/incidents", headers=identities[0]["headers"]
    )
    assert own_incidents.status_code == 200
    assert own_incidents.json()["items"][0]["id"] == incident["id"]
    other_incidents = await client.get(
        "/api/v1/pilots/me/incidents", headers=identities[1]["headers"]
    )
    assert other_incidents.status_code == 200 and other_incidents.json()["items"] == []

    staff_incidents = await client.get(
        f"/api/v1/operations/cities/{state['city']['id']}/pilot-incidents",
        headers=state["admin"]["headers"],
    )
    assert staff_incidents.status_code == 200, staff_incidents.text
    assert any(row["id"] == incident["id"] for row in staff_incidents.json()["items"])
    acknowledge = await client.post(
        f"/api/v1/operations/pilot-incidents/{incident['id']}/acknowledge",
        headers=state["admin"]["headers"],
    )
    assert acknowledge.status_code == 200 and acknowledge.json()["status"] == "acknowledged"
    denied_ack = await client.post(
        f"/api/v1/operations/pilot-incidents/{incident['id']}/acknowledge",
        headers=identities[1]["headers"],
    )
    assert denied_ack.status_code == 403
    resolved = await client.post(
        f"/api/v1/operations/pilot-incidents/{incident['id']}/resolve",
        json={
            "resolution_summary": (
                "Operations reviewed the report and confirmed the pilot is safe to return."
            )
        },
        headers=state["admin"]["headers"],
    )
    assert resolved.status_code == 200 and resolved.json()["status"] == "resolved"
    resumed = await client.post(
        "/api/v1/pilots/me/availability",
        json={"state": "online_available"},
        headers=identities[0]["headers"],
    )
    assert resumed.status_code == 200


async def test_balanced_journals_and_database_immutability(api):
    client, app = api
    state = await world(client, app, 1)
    org = state["shops"][0]["organization"]["id"]
    entity = await post(
        client,
        f"/organizations/{org}/legal-entities",
        {
            "country_id": state["country_id"],
            "registered_name": "Integration legal entity",
            "registration_reference": uuid4().hex,
        },
        state["shops"][0]["merchant"],
    )
    book = await post(
        client,
        "/finance/books",
        {"organization_id": org, "legal_entity_id": entity["id"], "currency": "XTS"},
        state["admin"],
    )
    accounts = [
        await post(
            client,
            "/finance/accounts",
            {
                "organization_id": org,
                "book_id": book["id"],
                "currency": "XTS",
                "code": code,
                "kind": kind,
            },
            state["admin"],
        )
        for code, kind in [("cash", "asset"), ("merchant_payable", "liability")]
    ]
    body = {
        "organization_id": org,
        "idempotency_key": uuid4().hex,
        "description": "Integration journal",
        "lines": [
            {"account_id": accounts[0]["id"], "amount": "10"},
            {"account_id": accounts[1]["id"], "amount": "-9"},
        ],
    }
    invalid = await client.post(
        "/api/v1/finance/journals", json=body, headers=state["admin"]["headers"]
    )
    assert invalid.status_code == 422
    body["lines"][1]["amount"] = "-10"
    journal = await post(client, "/finance/journals", body, state["admin"])
    assert journal["status"] == "posted"
    repeated = await post(client, "/finance/journals", body, state["admin"])
    assert repeated["id"] == journal["id"]
    with pytest.raises(DBAPIError):
        async with app.state.sessions.begin() as db:
            await db.execute(
                update(m.Journal)
                .where(m.Journal.id == UUID(journal["id"]))
                .values(description="illegal edit")
            )
    with pytest.raises(DBAPIError):
        async with app.state.sessions.begin() as db:
            raw = await add(
                db,
                m.Journal,
                organization_id=UUID(org),
                book_id=UUID(book["id"]),
                status="draft",
                idempotency_key=uuid4().hex,
                description="DB constraint test",
            )
            await add(
                db,
                m.JournalLine,
                journal_id=raw.id,
                organization_id=UUID(org),
                account_id=UUID(accounts[0]["id"]),
                currency="XTS",
                amount=Decimal("2"),
            )
            await add(
                db,
                m.JournalLine,
                journal_id=raw.id,
                organization_id=UUID(org),
                account_id=UUID(accounts[1]["id"]),
                currency="XTS",
                amount=Decimal("-1"),
            )
            raw.status = (
                "posted"  # Deferred constraint must fail at commit, even bypassing service.
            )
    reversal = await client.post(
        f"/api/v1/finance/journals/{journal['id']}/reversal",
        headers={**state["admin"]["headers"], "Idempotency-Key": uuid4().hex},
    )
    assert reversal.status_code == 201


async def test_sandbox_webhook_deduplication_and_partial_refund(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    payment = await post(
        client, "/finance/sandbox/payment-intents", {"order_id": order["id"]}, state["customer"]
    )
    payload = json.dumps(
        {
            "payment_id": payment["id"],
            "event_id": "SANDBOX:" + uuid4().hex,
            "amount": payment["amount"],
            "currency": "XTS",
            "status": "confirmed",
        }
    ).encode()
    signature = hmac.new(
        app.state.settings.sandbox_webhook_secret.get_secret_value().encode(), payload, "sha256"
    ).hexdigest()
    for _ in range(2):
        response = await client.post(
            "/api/v1/finance/sandbox/webhook",
            content=payload,
            headers={"X-Sandbox-Signature": signature},
        )
        assert response.status_code == 200, response.text
    body = {
        "organization_id": state["shops"][0]["organization"]["id"],
        "amount": "3",
        "idempotency_key": uuid4().hex,
    }
    approval = await post(
        client,
        "/finance/refund-approvals",
        {
            "organization_id": body["organization_id"],
            "order_id": order["id"],
            "amount": body["amount"],
        },
        state["shops"][0]["merchant"],
    )
    await post(
        client,
        f"/finance/refund-approvals/{approval['id']}/decision",
        {"decision": "approved", "reason": "Test-only refund approved separately"},
        state["admin"],
        200,
    )
    body["approval_id"] = approval["id"]
    refund = await post(
        client, f"/finance/sandbox/payments/{payment['id']}/refunds", body, state["admin"]
    )
    repeated = await post(
        client, f"/finance/sandbox/payments/{payment['id']}/refunds", body, state["admin"]
    )
    assert refund["id"] == repeated["id"]
    assert refund["status"] == "sandbox_confirmed"
    async with app.state.sessions() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(m.Webhook)
                .where(m.Webhook.payment_id == UUID(payment["id"]))
            )
            == 1
        )
        assert (await db.get(m.PaymentIntent, UUID(payment["id"]))).refunded == 3


async def test_outbox_consumer_retry_rollback_and_dedupe(api):
    _, app = api
    eid = uuid4()

    async def failing(db, payload):
        raise RuntimeError("transient test failure")

    with pytest.raises(RuntimeError):
        async with app.state.sessions.begin() as db:
            await events.consume(db, "integration-test", eid, failing, {})
    calls = []

    async def handler(db, payload):
        calls.append(payload)

    async with app.state.sessions.begin() as db:
        assert await events.consume(db, "integration-test", eid, handler, {"version": 1})
    async with app.state.sessions.begin() as db:
        assert not await events.consume(db, "integration-test", eid, handler, {"version": 1})
    assert len(calls) == 1


async def test_pagination_validation_and_fresh_migration(api):
    client, app = api
    identity = await user(client, app)
    for _ in range(3):
        await post(client, "/carts", None, identity)
    invalid = await client.get("/api/v1/orders?limit=1000", headers=identity["headers"])
    assert invalid.status_code == 422
    invalid_cursor = await client.get("/api/v1/orders?cursor=invalid", headers=identity["headers"])
    assert invalid_cursor.status_code == 422
    async with app.state.sessions() as db:
        assert await db.scalar(text("SELECT version_num FROM alembic_version")) == "20261027_0017"
        count = await db.scalar(
            text(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema IN "
                "('identity','geo','merchant','catalog','inventory','commerce','fulfillment',"
                "'finance','engagement','operations','intelligence','integration','audit') "
                "AND table_type='BASE TABLE'"
            )
        )
        assert count >= 246
