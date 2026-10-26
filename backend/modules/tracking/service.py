"""Validated GPS ingestion. PostgreSQL remains authoritative; Redis is a hot cache."""

import math
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.application.common import add, now
from backend.domain.rules import BusinessError
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F


def distance_m(lat1, lon1, lat2, lon2):
    """Spherical distance for plausibility checks only; never for serviceability/routing."""
    radius = 6_371_000
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dlat, dlon = p2 - p1, math.radians(float(lon2) - float(lon1))
    value = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


async def ingest_location(session, actor, values, settings):
    pilot = await session.scalar(
        select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)).with_for_update()
    )
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile before tracking", 403)
    if not pilot.location_consent_at:
        raise BusinessError(
            "location_consent_required",
            "Review and accept the pilot location policy before sending location",
            403,
        )
    observed = values.observed_at
    instant = now()
    if observed.tzinfo is None or observed > instant + timedelta(seconds=30):
        raise BusinessError(
            "invalid_location_time", "Location timestamp must be recent and offset-aware", 422
        )
    if observed < instant - timedelta(minutes=5):
        raise BusinessError("stale_location", "Location timestamp is too old", 422)
    if values.accuracy_m > 100:
        return {"accepted": False, "reason": "poor_accuracy", "sequence": values.client_sequence}

    current = await session.scalar(
        select(m.LatestLocation).where(m.LatestLocation.pilot_id == pilot.id).with_for_update()
    )
    if current and (
        values.client_sequence <= current.client_sequence or observed <= current.observed_at
    ):
        return {"accepted": False, "reason": "out_of_order", "sequence": current.client_sequence}
    if current:
        elapsed = (observed - current.observed_at).total_seconds()
        inferred = distance_m(
            current.latitude, current.longitude, values.latitude, values.longitude
        )
        if elapsed <= 0 or inferred / elapsed > 70:
            # Quarantined by rejection; no automatic punitive action or fraud conclusion.
            raise BusinessError("location_quarantined", "Location jump requires review", 422)

    data = values.model_dump()
    data["observed_at"] = observed
    write = insert(m.LatestLocation).values(pilot_id=pilot.id, **data)
    result_id = await session.scalar(
        write.on_conflict_do_update(
            index_elements=["pilot_id"],
            set_=data,
            where=(m.LatestLocation.client_sequence < write.excluded.client_sequence)
            & (m.LatestLocation.observed_at < write.excluded.observed_at),
        ).returning(m.LatestLocation.id)
    )
    if result_id is None:
        latest_sequence = await session.scalar(
            select(m.LatestLocation.client_sequence).where(m.LatestLocation.pilot_id == pilot.id)
        )
        return {
            "accepted": False,
            "reason": "out_of_order",
            "sequence": latest_sequence,
        }

    event_model = F["fulfillment.pilot_location_events"]
    last_saved = await session.scalar(
        select(event_model.observed_at)
        .where(event_model.pilot_id == pilot.id)
        .order_by(event_model.observed_at.desc())
        .limit(1)
    )
    sampled = (
        last_saved is None
        or (observed - last_saved).total_seconds()
        >= settings.pilot_location_history_interval_seconds
    )
    if sampled:
        await add(
            session,
            event_model,
            pilot_id=pilot.id,
            latitude=values.latitude,
            longitude=values.longitude,
            observed_at=observed,
            accuracy_m=values.accuracy_m,
            heading_degrees=values.heading_degrees,
            speed_mps=values.speed_mps,
            client_sequence=values.client_sequence,
            battery_percent=values.battery_percent,
            app_state=values.app_state,
            expires_at=instant + timedelta(days=settings.pilot_location_retention_days),
        )
    await session.flush()
    return {
        "accepted": True,
        "sampled": sampled,
        "sequence": values.client_sequence,
        "pilot_id": str(pilot.id),
        "city_id": str(pilot.city_id),
    }


async def cache_location(redis, result, values, ttl):
    """Maintain city GEO index and metadata with expiry; fail-soft after durable commit."""
    key = f"quickbuddy:tracking:city:{result['city_id']}:pilots"
    member = result["pilot_id"]
    async with redis.pipeline(transaction=True) as pipe:
        pipe.geoadd(key, (float(values.longitude), float(values.latitude), member))
        pipe.hset(
            f"quickbuddy:tracking:pilot:{member}",
            mapping={
                "observed_at": values.observed_at.isoformat(),
                "sequence": values.client_sequence,
            },
        )
        pipe.expire(key, ttl)
        pipe.expire(f"quickbuddy:tracking:pilot:{member}", ttl)
        await pipe.execute()


async def clear_cached_presence(redis, pilot_id, city_id):
    await redis.zrem(f"quickbuddy:tracking:city:{city_id}:pilots", str(pilot_id))
    await redis.delete(f"quickbuddy:tracking:pilot:{pilot_id}")


def issue_ticket():
    import hashlib
    import secrets

    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest(), uuid4()
