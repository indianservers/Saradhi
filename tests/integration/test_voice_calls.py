import asyncio
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from backend.application.common import add, now
from backend.persistence import models as m
from tests.integration.helpers import checkout, post, user, world


@pytest.fixture
async def voice_world(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    pilot = await user(client, app)
    outsider = await user(client, app)
    async with app.state.sessions.begin() as db:
        profile = await add(
            db,
            m.Pilot,
            user_id=UUID(pilot["id"]),
            city_id=UUID(state["city"]["id"]),
            verified=True,
            state="assigned",
        )
        unit = await db.scalar(
            select(m.FulfillmentUnit)
            .join(m.MerchantOrder)
            .where(m.MerchantOrder.order_id == UUID(order["id"]))
        )
        task = await db.scalar(
            select(m.DeliveryTask).where(m.DeliveryTask.fulfillment_unit_id == unit.id)
        )
        task.status = "assigned"
        assignment = await add(
            db,
            m.Assignment,
            task_id=task.id,
            pilot_id=profile.id,
            status="accepted",
            expires_at=now() + timedelta(minutes=5),
        )
        state.update(task_id=str(task.id), assignment_id=str(assignment.id))
    return client, app, state, pilot, outsider


async def send(client, call_id, identity, kind, payload, event_id=None):
    return await client.post(
        f"/api/v1/calls/{call_id}/signals",
        headers=identity["headers"],
        json={
            "client_event_id": event_id or str(uuid4()),
            "kind": kind,
            "payload": payload,
        },
    )


async def test_bidirectional_call_authorization_signaling_and_delivery_end(voice_world):
    client, app, state, pilot, outsider = voice_world
    customer = state["customer"]
    assert (await client.get("/api/v1/calls/active")).status_code == 401
    call = await post(client, "/calls", {"delivery_id": state["task_id"]}, customer)
    cid = call["id"]
    incoming = await client.get("/api/v1/calls/active", headers=pilot["headers"])
    assert incoming.json()["items"][0]["incoming"] is True
    assert not (await client.get("/api/v1/calls/active", headers=outsider["headers"])).json()[
        "items"
    ]
    assert (
        await client.get(f"/api/v1/calls/{cid}", headers=outsider["headers"])
    ).status_code == 404
    denied = await client.post(
        f"/api/v1/calls/{cid}/actions", headers=customer["headers"], json={"action": "accept"}
    )
    assert denied.status_code == 403
    offer = {"type": "offer", "sdp": "v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\n"}
    assert (await send(client, cid, outsider, "offer", offer)).status_code == 404
    assert (await send(client, cid, pilot, "offer", offer)).status_code == 403
    event_id = str(uuid4())
    assert (await send(client, cid, customer, "offer", offer, event_id)).status_code == 201
    assert (await send(client, cid, customer, "offer", offer, event_id)).status_code == 201
    own = await client.get(f"/api/v1/calls/{cid}/signals", headers=customer["headers"])
    assert own.json()["items"] == []
    received = await client.get(f"/api/v1/calls/{cid}/signals", headers=pilot["headers"])
    assert len(received.json()["items"]) == 1
    assert received.json()["items"][0]["payload"] == offer
    accepted = await post(client, f"/calls/{cid}/actions", {"action": "accept"}, pilot, 200)
    assert accepted["status"] == "active"
    answer = {"type": "answer", "sdp": "v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\n"}
    assert (await send(client, cid, pilot, "answer", answer)).status_code == 201
    assert (await send(client, cid, customer, "answer", answer)).status_code == 403
    busy = await client.post(
        "/api/v1/calls", headers=pilot["headers"], json={"delivery_id": state["task_id"]}
    )
    assert busy.status_code == 409
    async with app.state.sessions.begin() as db:
        task = await db.get(m.DeliveryTask, UUID(state["task_id"]))
        task.status = "delivered"
    ended = await client.get(f"/api/v1/calls/{cid}", headers=customer["headers"])
    assert ended.json()["status"] == "ended" and ended.json()["ice_servers"] == []
    assert (await send(client, cid, pilot, "answer", answer)).status_code == 409
    async with app.state.sessions() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(m.VoiceSignal)
                .where(m.VoiceSignal.call_id == UUID(cid))
            )
            == 0
        )


async def test_reverse_call_decline_expiry_and_reassignment(voice_world):
    client, app, state, pilot, outsider = voice_world
    customer = state["customer"]
    call = await post(client, "/calls", {"delivery_id": state["task_id"]}, pilot)
    assert not call["incoming"]
    incoming = (await client.get("/api/v1/calls/active", headers=customer["headers"])).json()
    assert incoming["items"][0]["incoming"]
    declined = await post(
        client, f"/calls/{call['id']}/actions", {"action": "decline"}, customer, 200
    )
    assert declined["status"] == "declined"
    call = await post(client, "/calls", {"delivery_id": state["task_id"]}, customer)
    async with app.state.sessions.begin() as db:
        row = await db.get(m.VoiceCall, UUID(call["id"]))
        row.expires_at = now() - timedelta(seconds=1)
    missed = await client.get(f"/api/v1/calls/{call['id']}", headers=pilot["headers"])
    assert missed.json()["status"] == "missed"
    call = await post(client, "/calls", {"delivery_id": state["task_id"]}, customer)
    async with app.state.sessions.begin() as db:
        assignment = await db.get(m.Assignment, UUID(state["assignment_id"]))
        assignment.status = "rejected"
    revoked = await client.get(f"/api/v1/calls/{call['id']}", headers=pilot["headers"])
    assert revoked.json()["status"] == "ended"
    forbidden = await client.post(
        "/api/v1/calls", headers=outsider["headers"], json={"delivery_id": state["task_id"]}
    )
    assert forbidden.status_code == 404


async def test_simultaneous_call_attempts_and_audio_only_validation(voice_world):
    client, _, state, pilot, _ = voice_world
    responses = await asyncio.gather(
        *[
            client.post(
                "/api/v1/calls", headers=identity["headers"], json={"delivery_id": state["task_id"]}
            )
            for identity in [state["customer"], pilot]
        ]
    )
    assert sorted(r.status_code for r in responses) == [201, 409]
    response = next(r for r in responses if r.status_code == 201)
    video = {"type": "offer", "sdp": "v=0\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\n"}
    invalid = await send(client, response.json()["id"], state["customer"], "offer", video)
    assert invalid.status_code == 422
