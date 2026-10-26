from uuid import uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError

from backend.application.common import add
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from tests.integration.helpers import checkout, user, world


async def test_customer_directory_and_360_are_scoped_masked_and_paginated(api):
    client, app = api
    state = await world(client, app, 1)
    customer = state["customer"]
    async with app.state.sessions.begin() as db:
        profile = F["identity.user_profiles"]
        current = await db.scalar(select(profile).where(profile.user_id == customer["id"]))
        if current:
            current.display_name = "CRM Test Customer"
        else:
            await add(
                db, profile, user_id=customer["id"], display_name="CRM Test Customer", locale="en"
            )
    await checkout(client, customer, state["shops"])

    directory = await client.get(
        f"/api/v1/admin/customers?city_id={state['city']['id']}&q=CRM%20Test&limit=1",
        headers=state["admin"]["headers"],
    )
    assert directory.status_code == 200, directory.text
    data = directory.json()
    row = next(item for item in data["items"] if item["id"] == customer["id"])
    assert row["name"] == "CRM Test Customer"
    assert row["email"] != customer["email"]
    assert "***@" in row["email"]
    assert row["order_count"] == 1

    detail = await client.get(
        f"/api/v1/admin/customers/{customer['id']}", headers=state["admin"]["headers"]
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["summary"]["order_count"] == 1
    orders = await client.get(
        f"/api/v1/admin/customers/{customer['id']}/orders?limit=1",
        headers=state["admin"]["headers"],
    )
    assert orders.status_code == 200, orders.text
    assert len(orders.json()["items"]) == 1

    for tab in (
        "payments",
        "addresses",
        "subscriptions",
        "loyalty",
        "referrals",
        "campaigns",
        "support",
        "feedback",
        "privacy",
        "security",
    ):
        response = await client.get(
            f"/api/v1/admin/customers/{customer['id']}/{tab}",
            headers=state["admin"]["headers"],
        )
        assert response.status_code == 200, f"{tab}: {response.text}"

    exported = await client.get(
        f"/api/v1/admin/customers-export?city_id={state['city']['id']}&purpose=customer_directory",
        headers=state["admin"]["headers"],
    )
    assert exported.status_code == 200, exported.text
    assert customer["email"] not in exported.text
    assert "CRM Test Customer" in exported.text
    assert "no-store" in exported.headers["cache-control"]

    consent = await client.post(
        "/api/v1/me/consents",
        json={"channel": "push", "enabled": False, "policy_version": "privacy-v1"},
        headers={
            **customer["headers"],
            "Idempotency-Key": "segment-consent-" + uuid4().hex,
        },
    )
    assert consent.status_code == 200, consent.text
    segment = await client.post(
        "/api/v1/admin/customer-segments/preview",
        json={
            "city_id": state["city"]["id"],
            "logic": "and",
            "conditions": [
                {"field": "order_count", "op": "gte", "value": 1},
                {
                    "field": "marketing_consent",
                    "op": "eq",
                    "value": False,
                    "channel": "push",
                },
            ],
        },
        headers=state["admin"]["headers"],
    )
    assert segment.status_code == 200, segment.text
    assert segment.json()["matched_count"] == 1


async def test_customer_admin_denies_unprivileged_identity(api):
    client, app = api
    stranger = await user(client, app)
    response = await client.get(
        "/api/v1/admin/customers?city_id=00000000-0000-0000-0000-000000000001",
        headers=stranger["headers"],
    )
    assert response.status_code == 403


async def test_customer_consent_is_self_owned_verified_and_append_only(api):
    client, app = api
    customer = await user(client, app)
    state = await client.get("/api/v1/me/consents", headers=customer["headers"])
    assert state.status_code == 200
    assert state.json()["items"] == []

    unverified_email = await client.post(
        "/api/v1/me/consents",
        json={"channel": "email", "enabled": True, "policy_version": "privacy-v1"},
        headers={
            **customer["headers"],
            "Idempotency-Key": "crm-consent-email-" + uuid4().hex,
        },
    )
    assert unverified_email.status_code == 409

    opt_in_key = "crm-consent-push-" + uuid4().hex
    headers = {**customer["headers"], "Idempotency-Key": opt_in_key}
    opted_in = await client.post(
        "/api/v1/me/consents",
        json={"channel": "push", "enabled": True, "policy_version": "privacy-v1"},
        headers=headers,
    )
    assert opted_in.status_code == 200, opted_in.text
    replay = await client.post(
        "/api/v1/me/consents",
        json={"channel": "push", "enabled": True, "policy_version": "privacy-v1"},
        headers=headers,
    )
    assert replay.json()["replayed"] is True

    opted_out = await client.post(
        "/api/v1/me/consents",
        json={"channel": "push", "enabled": False, "policy_version": "privacy-v1"},
        headers={
            **customer["headers"],
            "Idempotency-Key": "crm-consent-push-" + uuid4().hex,
        },
    )
    assert opted_out.status_code == 200
    state = await client.get("/api/v1/me/consents", headers=customer["headers"])
    assert state.json()["items"][0]["enabled"] is False

    async with app.state.sessions() as db:
        consent = await db.scalar(
            select(m.CustomerConsentEvent).where(
                m.CustomerConsentEvent.idempotency_key == opt_in_key
            )
        )
        consent_id = consent.id
    with pytest.raises(DBAPIError):
        async with app.state.sessions.begin() as db:
            await db.execute(
                update(m.CustomerConsentEvent)
                .where(m.CustomerConsentEvent.id == consent_id)
                .values(enabled=False)
            )
