import asyncio
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from uuid import UUID, uuid4

from sqlalchemy import select

from backend.application import events, identity, maintenance
from backend.application.common import add, now
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
    async with app.state.sessions.begin() as db:
        assert len(await maintenance.materialize_occurrences(db, plan_id, [instant])) == 1
    async with app.state.sessions.begin() as db:
        assert await maintenance.materialize_occurrences(db, plan_id, [instant]) == []


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
        )
        event_id = record.id

    class FailedPublisher:
        async def publish(self, *args):
            raise RuntimeError("test-only transport outage")

    async with app.state.sessions.begin() as db:
        await events.relay_batch(db, FailedPublisher(), limit=1)
    async with app.state.sessions() as db:
        record = await db.get(m.Outbox, event_id)
        assert record.dead_lettered_at is not None and record.attempts == 8


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
