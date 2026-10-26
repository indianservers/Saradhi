import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from uuid import UUID, uuid4

from sqlalchemy import func, select

from backend.application import events, identity, logistics, maintenance
from backend.application.common import add, now
from backend.integrations.maps.routing import FixtureRoutingProvider, RouteResult
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.shared.auth import Principal
from tests.integration.helpers import checkout, post, user, world


async def test_otp_limits_hashing_one_time_and_expiration(api):
    client, app = api
    actor = await user(client, app)

    class TestProvider:
        def __init__(self):
            self.code = None

        async def send(self, destination_reference, otp):
            self.code = otp

    provider = TestProvider()
    app.state.otp_provider = provider
    challenge = await post(client, "/auth/challenges", {"purpose": "verify_email"}, actor)
    assert provider.code is not None
    async with app.state.sessions() as db:
        record = await db.get(m.Challenge, UUID(challenge["id"]))
        assert record.digest != provider.code
        assert len(record.digest) == 64
    throttled = await client.post(
        "/api/v1/auth/challenges", json={"purpose": "verify_email"}, headers=actor["headers"]
    )
    assert throttled.status_code == 429
    consume = f"/api/v1/auth/challenges/{challenge['id']}/consume"
    for _ in range(5):
        bad = await client.post(consume, json={"code": "xxxxxx"}, headers=actor["headers"])
        assert bad.status_code == 401
    rejected = await client.post(consume, json={"code": provider.code}, headers=actor["headers"])
    assert rejected.status_code == 401
    # A fresh challenge is created with the application service after moving only this
    # dedicated test fixture's timestamp. No development data is changed.
    async with app.state.sessions.begin() as db:
        record = await db.get(m.Challenge, UUID(challenge["id"]))
        record.created_at = now() - timedelta(minutes=2)
    challenge = await post(client, "/auth/challenges", {"purpose": "verify_email"}, actor)
    consume = f"/api/v1/auth/challenges/{challenge['id']}/consume"
    success = await client.post(consume, json={"code": provider.code}, headers=actor["headers"])
    assert success.status_code == 204
    replay = await client.post(consume, json={"code": provider.code}, headers=actor["headers"])
    assert replay.status_code == 401
    async with app.state.sessions() as db:
        assert (
            await db.scalar(select(m.Email.verified_at).where(m.Email.user_id == UUID(actor["id"])))
            is not None
        )


async def test_shared_durable_auth_rate_limit(api):
    _, app = api
    subject = uuid4().hex
    async with app.state.sessions.begin() as db:
        assert await identity.rate_limit(db, subject, subject, limit=1)
    async with app.state.sessions.begin() as db:
        assert not await identity.rate_limit(db, subject, subject, limit=1)


async def test_pilot_location_is_authenticated_ordered_and_sampled(api):
    client, app = api
    state = await world(client, app, 1)
    pilot_user = await user(client, app)
    pilot = await post(client, "/pilots", {"city_id": state["city"]["id"]}, pilot_user)
    await post(client, f"/pilots/{pilot['id']}/verify", None, state["admin"], 200)
    consent = await client.post(
        "/api/v1/pilots/me/location-consent",
        json={"accepted": True, "policy_version": "pilot-location-v1"},
        headers=pilot_user["headers"],
    )
    assert consent.status_code == 200
    body = {
        "latitude": "17.3850000",
        "longitude": "78.4867000",
        "observed_at": now().isoformat(),
        "accuracy_m": "9.5",
        "heading_degrees": "180",
        "speed_mps": "2.5",
        "client_sequence": 1,
        "battery_percent": 80,
        "app_state": "foreground",
    }
    first = await client.post(
        "/api/v1/pilots/me/location", json=body, headers=pilot_user["headers"]
    )
    assert first.status_code == 200 and first.json()["accepted"]
    repeated = await client.post(
        "/api/v1/pilots/me/location", json=body, headers=pilot_user["headers"]
    )
    assert repeated.status_code == 200
    assert repeated.json()["accepted"] is False
    assert repeated.json()["reason"] == "out_of_order"
    invalid = await client.post(
        "/api/v1/pilots/me/location",
        json={**body, "latitude": "91", "client_sequence": 2},
        headers=pilot_user["headers"],
    )
    assert invalid.status_code == 422
    poor = await client.post(
        "/api/v1/pilots/me/location",
        json={**body, "accuracy_m": "180", "client_sequence": 2},
        headers=pilot_user["headers"],
    )
    assert poor.status_code == 200 and poor.json()["reason"] == "poor_accuracy"
    timings_ms = []
    for sequence in range(2, 32):
        sample = {
            **body,
            "client_sequence": sequence,
            "observed_at": now().isoformat(),
            "longitude": body["longitude"],
        }
        started = perf_counter()
        response = await client.post(
            "/api/v1/pilots/me/location", json=sample, headers=pilot_user["headers"]
        )
        timings_ms.append((perf_counter() - started) * 1000)
        assert response.status_code == 200 and response.json()["accepted"]
    timings_ms.sort()
    evidence = {
        "scope": "local ASGI API + PostgreSQL, sequential controlled smoke",
        "samples": len(timings_ms),
        "elapsed_seconds": round(sum(timings_ms) / 1000, 4),
        "throughput_updates_per_second": round(len(timings_ms) / (sum(timings_ms) / 1000), 2),
        "latency_ms_p50": round(timings_ms[len(timings_ms) // 2], 2),
        "latency_ms_p95": round(
            timings_ms[min(len(timings_ms) - 1, int(len(timings_ms) * 0.95))], 2
        ),
        "limitations": "single process, one pilot, sequential; not a capacity or concurrency claim",
    }
    Path("docs/performance/gps-ingestion-smoke.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    online = await client.post(
        "/api/v1/pilots/me/availability",
        json={"state": "online_available"},
        headers=pilot_user["headers"],
    )
    assert online.status_code == 200
    async with app.state.sessions() as db:
        latest = await db.scalar(
            select(m.LatestLocation).where(m.LatestLocation.pilot_id == UUID(pilot["id"]))
        )
        event_model = F["fulfillment.pilot_location_events"]
        history_count = await db.scalar(
            select(func.count())
            .select_from(event_model)
            .where(event_model.pilot_id == UUID(pilot["id"]))
        )
        assert latest.client_sequence == 31 and latest.accuracy_m == Decimal("9.5")
        assert history_count == 1


async def test_eta_uses_provider_durations_and_materiality_cache(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    async with app.state.sessions.begin() as db:
        task, unit, child, branch = await logistics.task_context(
            db,
            await db.scalar(
                select(m.DeliveryTask.id)
                .join(m.FulfillmentUnit)
                .join(m.MerchantOrder)
                .where(m.MerchantOrder.order_id == UUID(order["id"]))
            ),
        )
        unit.delivery_method = "courier"
        unit.address_snapshot = {"latitude": "17.390", "longitude": "78.490"}
        child.status = "ready"
        task.status = "unassigned"
        task_id = task.id
        branch_point = (float(branch.latitude), float(branch.longitude))
        destination = (17.390, 78.490)
    unavailable = await client.get(
        f"/api/v1/deliveries/{task_id}/eta", headers=state["customer"]["headers"]
    )
    assert unavailable.status_code == 503
    app.state.routing_provider = FixtureRoutingProvider(
        {(branch_point, destination): RouteResult(1500, 420, "fixture-road", "fixture")}
    )
    response = await client.get(
        f"/api/v1/deliveries/{task_id}/eta", headers=state["customer"]["headers"]
    )
    assert response.status_code == 200
    result = response.json()
    assert result["source"] == "fixture-road"
    assert result["confidence"] == "fixture"
    assert result["distance_m"] == 1500
    ai_eta = await client.post(
        "/api/v1/ai/eta/predict",
        json={"task_id": str(task_id)},
        headers=state["customer"]["headers"],
    )
    assert ai_eta.status_code == 200
    assert ai_eta.json()["provenance"] == "deterministic_rule_with_routing_provider"
    async with app.state.sessions() as db:
        eta_model = F["fulfillment.eta_estimates"]
        assert (
            await db.scalar(
                select(func.count()).select_from(eta_model).where(eta_model.task_id == task_id)
            )
            == 1
        )


async def test_realtime_ticket_is_short_lived_and_capabilities_are_explicit(api):
    client, app = api
    actor = await user(client, app)
    response = await client.post("/api/v1/realtime/tickets", headers=actor["headers"])
    assert response.status_code == 201
    expires = datetime.fromisoformat(response.json()["expires_at"])
    assert 30 <= (expires - now()).total_seconds() <= 65
    capabilities = await client.get("/health/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.json()["postgis"] == "unavailable"
    assert capabilities.json()["road_routing"] == "unavailable"
    assert capabilities.json()["live_cross_instance_events"] is False


async def test_ai_forecast_is_explicitly_untrained_and_model_evaluation_is_data_gated(api):
    client, app = api
    state = await world(client, app, 1)
    forecast = await client.get(
        f"/api/v1/ai/demand/cities/{state['city']['id']}/forecast",
        headers=state["admin"]["headers"],
    )
    assert forecast.status_code == 200
    assert forecast.json()["provenance"] == "deterministic_rule"
    assert forecast.json()["model_status"] == "cold_start_fallback"
    assert forecast.json()["sample_count"] == 0
    zone_forecast = await client.get(
        f"/api/v1/ai/demand/zones/{state['zone']['id']}/forecast",
        headers=state["admin"]["headers"],
    )
    positioning = await client.get(
        f"/api/v1/ai/positioning/zones/{state['zone']['id']}/recommendations",
        headers=state["admin"]["headers"],
    )
    assert zone_forecast.status_code == positioning.status_code == 200
    assert positioning.json()["zone_level_pilot_supply"] == "unavailable"
    models = await client.get("/api/v1/ai/models", headers=state["admin"]["headers"])
    assert models.status_code == 200
    assert models.json()["items"]
    assert all(row["status"] == "deterministic" for row in models.json()["items"])
    demand = next(
        row for row in models.json()["items"] if row["name"] == "quickbuddy-demand-baseline"
    )
    evaluation = await client.post(
        f"/api/v1/ai/models/{demand['model_id']}/evaluate",
        json={"city_id": state["city"]["id"]},
        headers=state["admin"]["headers"],
    )
    assert evaluation.status_code == 200
    assert evaluation.json()["sample_count"] == 0
    assert evaluation.json()["reason"] == "no_historical_orders"
    assert evaluation.json()["metrics"]["mae"] is None
    preparation = await client.post(
        "/api/v1/ai/preparation/predict",
        json={"branch_id": state["shops"][0]["branch"]["id"], "item_count": 2},
        headers=state["shops"][0]["merchant"]["headers"],
    )
    assert preparation.status_code == 200
    assert preparation.json()["provenance"] == "deterministic_rule"
    assert preparation.json()["expected_duration_minutes"] >= 16
    merchants = await client.post(
        "/api/v1/ai/recommendations/merchants",
        json={"city_id": state["city"]["id"]},
        headers=state["customer"]["headers"],
    )
    products = await client.post(
        "/api/v1/ai/recommendations/products",
        json={"city_id": state["city"]["id"]},
        headers=state["customer"]["headers"],
    )
    assert merchants.status_code == products.status_code == 200
    assert merchants.json()["personal_history_used"] is False
    assert products.json()["personal_history_used"] is False
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    risk = await client.get(
        f"/api/v1/ai/risk/orders/{order['id']}", headers=state["customer"]["headers"]
    )
    assert risk.status_code == 200
    assert risk.json()["provenance"] == "deterministic_rule"
    assert risk.json()["risk_level"] == "normal"
    outsider = await user(client, app)
    denied_risk = await client.get(
        f"/api/v1/ai/risk/orders/{order['id']}", headers=outsider["headers"]
    )
    assert denied_risk.status_code == 403
    copilot_status = await client.get(
        "/api/v1/ai/copilot/status", headers=state["customer"]["headers"]
    )
    copilot = await client.post(
        "/api/v1/ai/copilot/query",
        json={"question": "Summarize delayed orders in my city"},
        headers=state["customer"]["headers"],
    )
    assert copilot_status.json()["provider_configured"] is False
    assert copilot.status_code == 503


async def test_unpaid_cancel_releases_capacity_and_stock(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    cancelled = await post(
        client, f"/orders/{order['id']}/cancel", {"expected_version": 1}, state["customer"], 200
    )
    assert cancelled["status"] == "cancelled"
    async with app.state.sessions() as db:
        stock = await db.get(m.Stock, UUID(state["shops"][0]["stock"]["id"]))
        window = await db.get(m.Window, UUID(state["shops"][0]["window"]["id"]))
        assert stock.reserved == 0 and window.reserved == 0
    again = await client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        json={"expected_version": 1},
        headers=state["customer"]["headers"],
    )
    assert again.status_code == 409


async def test_coupon_limit_and_recurring_occurrence_dedupe(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    uid = UUID(state["customer"]["id"])
    org = UUID(state["shops"][0]["organization"]["id"])
    async with app.state.sessions.begin() as db:
        campaign = await add(
            db,
            F["engagement.promotional_campaigns"],
            organization_id=org,
            funding_party_id=org,
            name="Integration campaign",
            starts_at=now() - timedelta(days=1),
            ends_at=now() + timedelta(days=1),
        )
        coupon = await add(
            db,
            F["engagement.coupons"],
            campaign_id=campaign.id,
            code=uuid4().hex,
            total_limit=1,
            per_user_limit=1,
            per_merchant_limit=1,
            redeemed=0,
            stackable=False,
        )
        coupon_id = coupon.id
        plan = await add(
            db,
            F["fulfillment.recurring_order_plans"],
            user_id=uid,
            cart_template={},
            timezone="UTC",
            active=True,
        )
        plan_id = plan.id
    actor = Principal(str(uid), frozenset())
    async with app.state.sessions.begin() as db:
        first = await maintenance.redeem_coupon(
            db,
            actor,
            coupon_id,
            UUID(order["id"]),
            UUID(state["shops"][0]["branch"]["id"]),
            Decimal("1"),
        )
        first_id = first.id
    async with app.state.sessions.begin() as db:
        repeated = await maintenance.redeem_coupon(
            db,
            actor,
            coupon_id,
            UUID(order["id"]),
            UUID(state["shops"][0]["branch"]["id"]),
            Decimal("1"),
        )
        assert repeated.id == first_id
    instant = now() + timedelta(days=1)
    instants = [instant + timedelta(days=offset) for offset in range(30)]
    async with app.state.sessions.begin() as db:
        assert len(await maintenance.materialize_occurrences(db, plan_id, instants)) == 30
    async with app.state.sessions.begin() as db:
        assert await maintenance.materialize_occurrences(db, plan_id, instants) == []
    async with app.state.sessions() as db:
        occurrence_model = F["fulfillment.scheduled_order_occurrences"]
        occurrences = (
            await db.scalars(select(occurrence_model).where(occurrence_model.plan_id == plan_id))
        ).all()
        assert len(occurrences) == 30
        assert all(row.order_id is None for row in occurrences)
        assert all(row.status == "awaiting_revalidation" for row in occurrences)
        assert all(row.revalidation_reason for row in occurrences)


async def test_distinct_addresses_create_distinct_fulfillment_units(api):
    client, app = api
    state = await world(client, app, 1)
    customer, shop = state["customer"], state["shops"][0]
    addresses = [
        await post(
            client,
            "/addresses",
            {
                "city_id": state["city"]["id"],
                "label": f"Destination {offset}",
                "address_text": f"Synthetic destination {offset}",
                "latitude": f"17.{3850000 + offset}",
                "longitude": "78.4867000",
            },
            customer,
        )
        for offset in (1, 2)
    ]
    cart = await post(client, "/carts", None, customer)
    for address in addresses:
        await post(
            client,
            f"/carts/{cart['id']}/items",
            {
                "branch_id": shop["branch"]["id"],
                "variant_id": shop["variant"]["id"],
                "quantity": "1",
                "window_id": shop["window"]["id"],
                "address_id": address["id"],
                # Courier serviceability requires PostGIS, which is absent locally.
                # Pickup preserves destination IDs for this grouping assertion.
                "delivery_method": "pickup",
            },
            customer,
        )
    quote = await post(client, f"/carts/{cart['id']}/quote", None, customer)
    order = await post(
        client,
        "/orders/confirm",
        {"quote_id": quote["id"]},
        customer,
        headers={"Idempotency-Key": uuid4().hex},
    )
    async with app.state.sessions() as db:
        units = (
            await db.scalars(
                select(m.FulfillmentUnit)
                .join(m.MerchantOrder)
                .where(m.MerchantOrder.order_id == UUID(order["id"]))
            )
        ).all()
        assert len(units) == 2
        assert {unit.address_snapshot["id"] for unit in units} == {
            address["id"] for address in addresses
        }


async def test_outbox_retry_deadletter_and_recovery_state(api):
    _, app = api
    event_id = None
    async with app.state.sessions.begin() as db:
        record = await add(
            db,
            m.Outbox,
            event_type="test.failure",
            aggregate_id=uuid4(),
            payload={"version": "1"},
            correlation_id="integration",
            attempts=7,
            created_at=now() - timedelta(days=365),
            available_at=now() - timedelta(days=365),
        )
        event_id = record.id

    class FailedPublisher:
        async def publish(self, *args):
            raise RuntimeError("test-only transport outage")

    await events.relay_batch(app.state.sessions, FailedPublisher(), limit=1)
    async with app.state.sessions() as db:
        record = await db.get(m.Outbox, event_id)
        assert record.dead_lettered_at is not None and record.attempts == 8


async def test_outbox_publisher_runs_after_claim_transaction_commits(api):
    _, app = api
    async with app.state.sessions.begin() as db:
        event = await add(
            db,
            m.Outbox,
            event_type="test.claimed",
            aggregate_id=uuid4(),
            payload={"version": "1"},
            correlation_id="integration",
            attempts=0,
            available_at=now() - timedelta(days=365),
        )
        event_id = event.id

    class InspectingPublisher:
        async def publish(self, received_id, aggregate_id, event_type, version, payload):
            assert received_id == str(event_id)
            assert aggregate_id
            # NOWAIT succeeds only if the committed claim transaction released its row lock.
            async with app.state.sessions.begin() as db:
                row = await db.scalar(
                    select(m.Outbox).where(m.Outbox.id == event_id).with_for_update(nowait=True)
                )
                assert row.claim_token is not None
                assert row.claim_expires_at > now()
                assert event_type == "test.claimed" and version == 1
                assert payload == {"version": "1"}

    assert await events.relay_batch(app.state.sessions, InspectingPublisher(), limit=1) >= 1
    async with app.state.sessions() as db:
        row = await db.get(m.Outbox, event_id)
        assert row.delivered_at is not None
        assert row.claim_token is None and row.claim_expires_at is None


async def test_delivery_failure_is_authorized_and_retention_prunes_only_expired(api):
    client, app = api
    actor = await user(client, app)
    async with app.state.sessions.begin() as db:
        # Real database cleanup test, deliberately no order data required.
        old = await add(
            db,
            m.RateBucket,
            bucket_key=uuid4().hex,
            window_start=now() - timedelta(days=2),
            attempts=1,
        )
        old_id = old.id
        fresh = await add(db, m.RateBucket, bucket_key=uuid4().hex, window_start=now(), attempts=1)
        fresh_id = fresh.id
    async with app.state.sessions.begin() as db:
        await maintenance.prune_ephemeral(db, limit=100000)
    async with app.state.sessions() as db:
        assert await db.get(m.RateBucket, old_id) is None
        assert await db.get(m.RateBucket, fresh_id) is not None
    denied = await client.post(
        f"/api/v1/delivery-tasks/{uuid4()}/fail",
        json={"expected_version": 1},
        headers=actor["headers"],
    )
    assert denied.status_code == 404


async def test_fefo_batch_reservation_rejects_stock_expiring_before_delivery(api):
    client, app = api
    state = await world(client, app, 1)
    shop = state["shops"][0]
    branch_id, variant_id = shop["branch"]["id"], shop["variant"]["id"]
    await post(
        client,
        f"/inventory/branches/{branch_id}/adjustments",
        {"variant_id": variant_id, "delta": "-10", "idempotency_key": uuid4().hex},
        shop["merchant"],
        200,
    )
    for code, days, quantity in [("too-soon", 1, "5"), ("valid", 7, "1")]:
        await post(
            client,
            f"/inventory/branches/{branch_id}/batches",
            {
                "variant_id": variant_id,
                "lot_code": code,
                "quantity": quantity,
                "expires_on": (now() + timedelta(days=days)).date().isoformat(),
                "idempotency_key": uuid4().hex,
            },
            shop["merchant"],
        )
    _, _, order, _ = await checkout(client, state["customer"], [shop])
    async with app.state.sessions() as db:
        Allocation, Batch = (
            F["inventory.batch_reservation_allocations"],
            F["inventory.stock_batches"],
        )
        allocation = await db.scalar(
            select(Allocation)
            .join(m.Reservation, Allocation.reservation_id == m.Reservation.id)
            .join(m.OrderItem)
            .join(m.MerchantOrder)
            .where(m.MerchantOrder.order_id == UUID(order["id"]))
        )
        batch = await db.get(Batch, allocation.batch_id)
        assert batch.lot_code == "valid" and batch.reserved == 1
    cart = await post(client, "/carts", None, state["customer"])
    await post(
        client,
        f"/carts/{cart['id']}/items",
        {
            "branch_id": branch_id,
            "variant_id": variant_id,
            "quantity": "1",
            "window_id": shop["window"]["id"],
        },
        state["customer"],
    )
    quote = await post(client, f"/carts/{cart['id']}/quote", None, state["customer"])
    denied = await client.post(
        "/api/v1/orders/confirm",
        json={"quote_id": quote["id"]},
        headers={**state["customer"]["headers"], "Idempotency-Key": uuid4().hex},
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "batch_stock_unavailable"
    await post(
        client, f"/orders/{order['id']}/cancel", {"expected_version": 1}, state["customer"], 200
    )
    async with app.state.sessions() as db:
        batch = await db.get(Batch, batch.id)
        assert batch.reserved == 0 and batch.quantity == 1


async def test_one_hundred_concurrent_checkout_transactions(api):
    client, app = api
    state = await world(client, app, 1)
    shop = state["shops"][0]
    await post(
        client,
        f"/inventory/branches/{shop['branch']['id']}/adjustments",
        {"variant_id": shop["variant"]["id"], "delta": "90", "idempotency_key": uuid4().hex},
        shop["merchant"],
        200,
    )
    quotes = []
    buyers = []
    for _ in range(100):
        buyer = await user(client, app)
        buyers.append(buyer)
        cart = await post(client, "/carts", None, buyer)
        await post(
            client,
            f"/carts/{cart['id']}/items",
            {
                "branch_id": shop["branch"]["id"],
                "variant_id": shop["variant"]["id"],
                "quantity": "1",
                "window_id": shop["window"]["id"],
            },
            buyer,
        )
        quotes.append(await post(client, f"/carts/{cart['id']}/quote", None, buyer))

    async def place(quote, buyer):
        return await client.post(
            "/api/v1/orders/confirm",
            json={"quote_id": quote["id"]},
            headers={**buyer["headers"], "Idempotency-Key": uuid4().hex},
        )

    start = perf_counter()
    results = await asyncio.gather(
        *(place(quote, buyer) for quote, buyer in zip(quotes, buyers, strict=True))
    )
    elapsed = perf_counter() - start
    counts = {
        str(code): sum(response.status_code == code for response in results)
        for code in {response.status_code for response in results}
    }
    Path("docs/operations/concurrency-evidence.json").write_text(
        json.dumps(
            {
                "database": "quickbuddy_test",
                "transport": "in-process ASGI with real PostgreSQL",
                "concurrent_requests": 100,
                "independent_authenticated_sessions": 100,
                "placed_orders": counts.get("201", 0),
                "statuses": counts,
                "elapsed_seconds": round(elapsed, 3),
                "confirmation_requests_per_second": round(100 / elapsed, 3),
                "scope": (
                    "100 customers, one branch, one shared stock row; "
                    "no provider, network, GPS or delivery throughput claim"
                ),
                "pool_size": app.state.settings.db_pool_size,
                "max_overflow": app.state.settings.db_max_overflow,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    assert counts == {"201": 100}, counts
    async with app.state.sessions() as db:
        stock = await db.get(m.Stock, UUID(shop["stock"]["id"]))
        window = await db.get(m.Window, UUID(shop["window"]["id"]))
        assert stock.on_hand == 100 and stock.reserved == 100
        assert window.reserved == 100
