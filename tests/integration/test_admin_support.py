from uuid import UUID, uuid4

from sqlalchemy import select

from backend.application.common import add
from backend.persistence import models as m
from tests.integration.helpers import post, user, world


async def test_support_claim_reply_and_resolve_are_owned_and_audited(api):
    client, app = api
    customer = await user(client, app)
    agent = await user(client, app, "support_agent")
    other_agent = await user(client, app, "support_agent")

    denied = await client.get("/api/v1/support/tickets", headers=customer["headers"])
    assert denied.status_code == 403

    created = await client.post(
        "/api/v1/support/tickets",
        json={"subject": "Missing item in delivery", "order_id": None},
        headers=customer["headers"],
    )
    assert created.status_code == 201, created.text
    ticket_id = created.json()["id"]
    customer_message = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        json={"body": "One item was missing from the bag."},
        headers=customer["headers"],
    )
    assert customer_message.status_code == 201

    queue = await client.get("/api/v1/support/tickets?limit=50", headers=agent["headers"])
    assert queue.status_code == 200, queue.text
    listed = next(row for row in queue.json()["items"] if row["id"] == ticket_id)
    assert listed["subject"] == "Missing item in delivery"
    assert "user_id" not in listed

    claimed = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/claim", headers=agent["headers"]
    )
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["assigned_to_me"] is True

    competing_claim = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/claim", headers=other_agent["headers"]
    )
    assert competing_claim.status_code == 409
    other_queue = await client.get("/api/v1/support/tickets", headers=other_agent["headers"])
    assert all(row["id"] != ticket_id for row in other_queue.json()["items"])

    conversation = await client.get(
        f"/api/v1/support/tickets/{ticket_id}/messages", headers=agent["headers"]
    )
    assert conversation.status_code == 200, conversation.text
    assert conversation.json()["items"][0]["author"] == "customer"
    assert conversation.json()["items"][0]["body"] == "One item was missing from the bag."

    reply = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        json={"body": "We are reviewing your report."},
        headers=agent["headers"],
    )
    assert reply.status_code == 201, reply.text
    resolved = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/resolve", headers=agent["headers"]
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    closed_reply = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        json={"body": "This should be rejected."},
        headers=customer["headers"],
    )
    assert closed_reply.status_code == 409

    async with app.state.sessions() as db:
        actions = set(
            (
                await db.scalars(
                    select(m.AuditEvent.action).where(m.AuditEvent.resource_id == UUID(ticket_id))
                )
            ).all()
        )
    assert {
        "support.ticket.read",
        "support.ticket_claim",
        "support.ticket_conversation.read",
        "support.ticket_reply",
        "support.ticket_resolve",
    } <= actions


async def test_org_scoped_support_agent_cannot_list_global_customer_tickets(api):
    client, app = api
    customer = await user(client, app)
    created = await client.post(
        "/api/v1/support/tickets",
        json={"subject": "Private customer issue", "order_id": None},
        headers=customer["headers"],
    )
    assert created.status_code == 201, created.text
    agent = await user(client, app)

    async with app.state.sessions.begin() as db:
        organization = await add(
            db, m.Organization, name="Scoped support " + uuid4().hex, owner_id=agent["id"]
        )
        await add(
            db,
            m.Membership,
            organization_id=organization.id,
            user_id=agent["id"],
            status="active",
        )
        role = await db.scalar(select(m.Role).where(m.Role.name == "support_agent"))
        await add(
            db,
            m.RoleAssignment,
            user_id=agent["id"],
            role_id=role.id,
            organization_id=organization.id,
        )

    queue = await client.get("/api/v1/support/tickets", headers=agent["headers"])
    assert queue.status_code == 200, queue.text
    assert all(row["id"] != created.json()["id"] for row in queue.json()["items"])


async def test_city_operator_picker_and_dispatch_are_city_scoped(api):
    client, app = api
    state = await world(client, app, count=1)
    other_city = await post(
        client,
        "/geo/cities",
        {
            "country_id": state["country_id"],
            "name": "Outside " + uuid4().hex,
            "timezone": "UTC",
        },
        state["admin"],
    )
    operator = await user(client, app)
    async with app.state.sessions.begin() as db:
        role = await db.scalar(select(m.Role).where(m.Role.name == "city_operator"))
        await add(
            db,
            m.RoleAssignment,
            user_id=operator["id"],
            role_id=role.id,
            city_id=state["city"]["id"],
        )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": operator["email"], "password": operator["password"]},
    )
    assert login.status_code == 200
    operator["headers"] = {"Authorization": "Bearer " + login.json()["access_token"]}

    city_list = await client.get(
        "/api/v1/operations/authorized-cities?limit=100", headers=operator["headers"]
    )
    assert city_list.status_code == 200, city_list.text
    assert [city["id"] for city in city_list.json()["items"]] == [state["city"]["id"]]
    allowed = await client.get(
        f"/api/v1/operations/cities/{state['city']['id']}/fleet",
        headers=operator["headers"],
    )
    denied = await client.get(
        f"/api/v1/operations/cities/{other_city['id']}/fleet",
        headers=operator["headers"],
    )
    assert allowed.status_code == 200
    assert denied.status_code == 403
