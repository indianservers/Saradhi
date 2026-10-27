"""Authenticated, assignment-bound WebRTC signaling. Audio never passes through this API."""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
from datetime import timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, model_validator
from sqlalchemy import case, delete, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert

from backend.api.v1.dependencies import DB, Actor
from backend.application.common import now
from backend.domain.rules import BusinessError
from backend.persistence import models as m

router = APIRouter(prefix="/api/v1/calls", tags=["Delivery voice calls"])
LIVE = {"ringing", "active"}


async def expire_signaling(sessions):
    """Remove expired session descriptions even if neither app reconnects."""
    while True:
        try:
            async with sessions.begin() as db:
                await db.execute(
                    update(m.VoiceCall)
                    .where(m.VoiceCall.expires_at <= now(), m.VoiceCall.status.in_(LIVE))
                    .values(
                        status=case((m.VoiceCall.status == "ringing", "missed"), else_="ended"),
                        ended_at=now(),
                    )
                )
                expired = select(m.VoiceCall.id).where(
                    or_(m.VoiceCall.expires_at <= now(), m.VoiceCall.status.not_in(LIVE))
                )
                await db.execute(
                    delete(m.VoiceSignal).where(
                        or_(
                            m.VoiceSignal.call_id.in_(expired),
                            m.VoiceSignal.created_at < now() - timedelta(hours=1),
                        )
                    )
                )
                await db.execute(
                    delete(m.VoiceCall).where(m.VoiceCall.expires_at < now() - timedelta(days=7))
                )
        except Exception:
            logging.getLogger(__name__).warning("Voice signaling cleanup unavailable")
        await asyncio.sleep(60)


class StartCall(BaseModel):
    delivery_id: UUID


class CallAction(BaseModel):
    action: Literal["accept", "decline", "end"]


class Signal(BaseModel):
    client_event_id: UUID
    kind: Literal["offer", "answer", "ice"]
    payload: dict

    @model_validator(mode="after")
    def bounded_payload(self):
        if len(json.dumps(self.payload).encode()) > 65536:
            raise ValueError("Signaling message is too large")
        if self.kind in {"offer", "answer"}:
            if set(self.payload) != {"sdp", "type"} or self.payload["type"] != self.kind:
                raise ValueError("Invalid session description")
            if not isinstance(self.payload["sdp"], str) or not self.payload["sdp"]:
                raise ValueError("Missing session description")
            if "m=video" in self.payload["sdp"] or "m=application" in self.payload["sdp"]:
                raise ValueError("Only audio calls are supported")
        else:
            if set(self.payload) - {"candidate", "sdpMid", "sdpMLineIndex"}:
                raise ValueError("Invalid ICE candidate")
            if not isinstance(self.payload.get("candidate"), str):
                raise ValueError("Missing ICE candidate")
            if self.payload.get("sdpMid") is not None and not isinstance(
                self.payload["sdpMid"], str
            ):
                raise ValueError("Invalid media identifier")
            index = self.payload.get("sdpMLineIndex")
            if index is not None and (type(index) is not int or index != 0):
                raise ValueError("Invalid audio media index")
        return self


def enabled(request):
    settings = request.app.state.settings
    if not settings.calling_enabled or (
        settings.app_env in {"staging", "production"} and not settings.call_turn_urls
    ):
        raise BusinessError("calling_unavailable", "App calling is temporarily unavailable", 503)


async def delivery_participants(db, delivery_id, user_id):
    row = (
        await db.execute(
            select(m.Assignment, m.Pilot, m.DeliveryTask, m.Order)
            .join(m.Pilot, m.Assignment.pilot_id == m.Pilot.id)
            .join(m.DeliveryTask, m.Assignment.task_id == m.DeliveryTask.id)
            .join(m.FulfillmentUnit, m.DeliveryTask.fulfillment_unit_id == m.FulfillmentUnit.id)
            .join(m.MerchantOrder, m.FulfillmentUnit.merchant_order_id == m.MerchantOrder.id)
            .join(m.Order, m.MerchantOrder.order_id == m.Order.id)
            .where(
                m.DeliveryTask.id == delivery_id,
                m.DeliveryTask.status.in_(["assigned", "picked_up"]),
                m.Assignment.status.in_(["accepted", "picked_up"]),
                m.Pilot.verified.is_(True),
                m.Pilot.state != "suspended",
                m.Order.status.not_in(["cancelled", "completed", "delivered", "failed"]),
                m.MerchantOrder.status.not_in(["cancelled", "rejected", "fulfilled"]),
                or_(m.Order.user_id == user_id, m.Pilot.user_id == user_id),
            )
        )
    ).one_or_none()
    if not row:
        raise BusinessError("call_delivery_unavailable", "No active assigned delivery to call", 404)
    assignment, pilot, task, order = row
    users = (
        await db.scalars(
            select(m.User.id).where(
                m.User.id.in_([pilot.user_id, order.user_id]), m.User.status == "active"
            )
        )
    ).all()
    if len(set(users)) != 2:
        raise BusinessError("call_delivery_unavailable", "Delivery calling is unavailable", 404)
    return assignment, pilot, task, order


async def refresh_call(db, call):
    if call.status not in LIVE:
        return
    try:
        assignment, pilot, _, order = await delivery_participants(db, call.task_id, call.caller_id)
        valid = assignment.id == call.assignment_id and {pilot.user_id, order.user_id} == {
            call.caller_id,
            call.recipient_id,
        }
    except BusinessError:
        valid = False
    if call.expires_at <= now() or not valid:
        call.status = "missed" if call.status == "ringing" and valid else "ended"
        call.ended_at = now()
        await db.execute(delete(m.VoiceSignal).where(m.VoiceSignal.call_id == call.id))


async def require_call(db, call_id, user_id):
    call = await db.scalar(
        select(m.VoiceCall)
        .where(
            m.VoiceCall.id == call_id,
            or_(m.VoiceCall.caller_id == user_id, m.VoiceCall.recipient_id == user_id),
        )
        .with_for_update()
    )
    if not call:
        raise BusinessError("call_not_found", "Call was not found", 404)
    await refresh_call(db, call)
    return call


def call_view(call, user_id):
    return {
        "id": str(call.id),
        "delivery_id": str(call.task_id),
        "status": call.status,
        "incoming": call.recipient_id == user_id,
        "expires_at": call.expires_at,
        "answered_at": call.answered_at,
    }


def ice_servers(settings, user_id):
    result = [{"urls": settings.call_stun_urls}] if settings.call_stun_urls else []
    secret = settings.call_turn_secret.get_secret_value()
    if settings.call_turn_urls and secret:
        username = f"{int((now() + timedelta(hours=1)).timestamp())}:{user_id}"
        credential = base64.b64encode(
            hmac.new(secret.encode(), username.encode(), hashlib.sha1).digest()
        ).decode()
        result.append(
            {"urls": settings.call_turn_urls, "username": username, "credential": credential}
        )
    return result


@router.get("/configuration")
async def configuration(actor: Actor, request: Request):
    settings = request.app.state.settings
    available = settings.calling_enabled and (
        settings.app_env in {"development", "test"} or bool(settings.call_turn_urls)
    )
    return {"enabled": available, "background_ringing": False}


@router.post("", status_code=201)
async def start(body: StartCall, actor: Actor, db: DB, request: Request):
    enabled(request)
    from backend.api.v1.routes import actor_budget

    await actor_budget(request, actor, "voice_call_start", limit=10)
    user_id = UUID(actor.subject)
    assignment, pilot, _, order = await delivery_participants(db, body.delivery_id, user_id)
    peer_id = pilot.user_id if user_id == order.user_id else order.user_id
    # Stable participant locks prevent simultaneous calls from separate app instances.
    for participant in sorted([user_id, peer_id]):
        key = int.from_bytes(
            hashlib.blake2b(participant.bytes, digest_size=8).digest(), signed=True
        )
        await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
    live = (
        await db.scalars(
            select(m.VoiceCall)
            .where(
                m.VoiceCall.status.in_(LIVE),
                or_(
                    m.VoiceCall.caller_id.in_([user_id, peer_id]),
                    m.VoiceCall.recipient_id.in_([user_id, peer_id]),
                ),
            )
            .with_for_update()
        )
    ).all()
    for existing in live:
        await refresh_call(db, existing)
        if existing.status in LIVE:
            if existing.caller_id == user_id and existing.assignment_id == assignment.id:
                return call_view(existing, user_id)
            raise BusinessError("call_busy", "One of you is already on a call", 409)
    call = m.VoiceCall(
        task_id=body.delivery_id,
        assignment_id=assignment.id,
        caller_id=user_id,
        recipient_id=peer_id,
        status="ringing",
        expires_at=now() + timedelta(seconds=45),
    )
    db.add(call)
    await db.flush()
    return call_view(call, user_id)


@router.get("/active")
async def active(actor: Actor, db: DB, request: Request):
    enabled(request)
    user_id = UUID(actor.subject)
    calls = (
        await db.scalars(
            select(m.VoiceCall)
            .where(
                m.VoiceCall.status.in_(LIVE),
                or_(m.VoiceCall.caller_id == user_id, m.VoiceCall.recipient_id == user_id),
            )
            .order_by(m.VoiceCall.created_at.desc())
            .limit(10)
            .with_for_update()
        )
    ).all()
    for call in calls:
        await refresh_call(db, call)
    return {"items": [call_view(call, user_id) for call in calls if call.status in LIVE]}


@router.get("/{call_id}")
async def get_call(call_id: UUID, actor: Actor, db: DB, request: Request):
    enabled(request)
    call = await require_call(db, call_id, UUID(actor.subject))
    return {
        **call_view(call, UUID(actor.subject)),
        "ice_servers": ice_servers(request.app.state.settings, actor.subject)
        if call.status in LIVE
        else [],
    }


@router.post("/{call_id}/actions")
async def action(call_id: UUID, body: CallAction, actor: Actor, db: DB, request: Request):
    enabled(request)
    user_id = UUID(actor.subject)
    call = await require_call(db, call_id, user_id)
    if call.status not in LIVE:
        return call_view(call, user_id)
    if body.action in {"accept", "decline"} and user_id != call.recipient_id:
        raise BusinessError("call_action_forbidden", "Only the recipient can answer this call", 403)
    if body.action == "accept":
        if call.status == "ringing":
            call.status, call.answered_at = "active", now()
            call.expires_at = now() + timedelta(minutes=30)
    else:
        call.status = "declined" if body.action == "decline" else "ended"
        call.ended_at = now()
        await db.execute(delete(m.VoiceSignal).where(m.VoiceSignal.call_id == call.id))
    return call_view(call, user_id)


@router.post("/{call_id}/signals", status_code=201)
async def signal(call_id: UUID, body: Signal, actor: Actor, db: DB, request: Request):
    enabled(request)
    user_id = UUID(actor.subject)
    call = await require_call(db, call_id, user_id)
    if call.status not in LIVE:
        raise BusinessError("call_ended", "This call has ended", 409)
    if (body.kind == "offer" and call.caller_id != user_id) or (
        body.kind == "answer" and (call.recipient_id != user_id or call.status != "active")
    ):
        raise BusinessError("call_signal_forbidden", "Invalid call signaling direction", 403)
    count = await db.scalar(
        select(func.count()).select_from(m.VoiceSignal).where(m.VoiceSignal.call_id == call.id)
    )
    if count >= 256:
        raise BusinessError("call_signal_limit", "Call signaling limit reached", 429)
    await db.execute(
        insert(m.VoiceSignal)
        .values(
            call_id=call.id,
            sender_id=user_id,
            client_event_id=body.client_event_id,
            kind=body.kind,
            payload=body.payload,
        )
        .on_conflict_do_nothing(index_elements=["call_id", "client_event_id"])
    )
    return {"accepted": True}


@router.get("/{call_id}/signals")
async def signals(
    call_id: UUID, actor: Actor, db: DB, request: Request, after: Annotated[int, Query(ge=0)] = 0
):
    enabled(request)
    user_id = UUID(actor.subject)
    call = await require_call(db, call_id, user_id)
    rows = (
        []
        if call.status not in LIVE
        else (
            await db.scalars(
                select(m.VoiceSignal)
                .where(
                    m.VoiceSignal.call_id == call.id,
                    m.VoiceSignal.id > after,
                    m.VoiceSignal.sender_id != user_id,
                )
                .order_by(m.VoiceSignal.id)
                .limit(100)
            )
        ).all()
    )
    return {
        "call": call_view(call, user_id),
        "items": [{"id": row.id, "kind": row.kind, "payload": row.payload} for row in rows],
    }
