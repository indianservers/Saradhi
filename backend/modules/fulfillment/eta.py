"""Versioned ETA calculation using road-provider durations, never degree-based estimates."""

from datetime import timedelta

from sqlalchemy import select

from backend.application.common import add, now
from backend.domain.rules import BusinessError
from backend.integrations.maps.routing import RoutingUnavailable
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F


async def estimate(session, task, unit, child, branch, provider, settings):
    model = F["fulfillment.eta_estimates"]
    prior = await session.scalar(
        select(model).where(model.task_id == task.id).order_by(model.generated_at.desc()).limit(1)
    )
    instant = now()
    if prior and prior.generated_at >= instant - timedelta(seconds=90):
        return {
            "pilot_arrival_at": None,
            "pickup_at": prior.pickup_at,
            "delivery_at": prior.delivery_at,
            "generated_at": prior.generated_at,
            "source": prior.source,
            "confidence": prior.confidence,
            "rule_version": prior.rule_version,
            "reason": "cached_route",
            "distance_m": None,
        }
    address = unit.address_snapshot
    if not address or "latitude" not in address or "longitude" not in address:
        raise BusinessError(
            "eta_destination_unavailable", "Delivery destination is unavailable", 409
        )
    destination = (float(address["latitude"]), float(address["longitude"]))
    pickup = (float(branch.latitude), float(branch.longitude))
    try:
        delivery_route = await provider.route(pickup, destination)
        pilot_arrival = None
        assignment = await session.scalar(
            select(m.Assignment)
            .where(
                m.Assignment.task_id == task.id, m.Assignment.status.in_(["accepted", "picked_up"])
            )
            .order_by(m.Assignment.created_at.desc())
            .limit(1)
        )
        if assignment:
            latest = await session.scalar(
                select(m.LatestLocation).where(m.LatestLocation.pilot_id == assignment.pilot_id)
            )
            if latest and latest.observed_at >= instant - timedelta(
                seconds=settings.pilot_location_fresh_seconds
            ):
                pickup_route = await provider.route(
                    (float(latest.latitude), float(latest.longitude)), pickup
                )
                pilot_arrival = instant + timedelta(seconds=pickup_route.duration_seconds)
    except RoutingUnavailable as exc:
        raise BusinessError("routing_unavailable", "Road ETA is unavailable", 503) from exc

    window = await session.get(m.Window, unit.window_id)
    merchant_ready = instant if child.status == "ready" else window.starts_at
    expected_pickup = max(pilot_arrival or instant, merchant_ready)
    pickup_at = expected_pickup + timedelta(seconds=settings.pickup_handling_seconds)
    delivery_at = pickup_at + timedelta(
        seconds=delivery_route.duration_seconds + settings.delivery_handling_seconds
    )
    changed = prior is None or abs((delivery_at - prior.delivery_at).total_seconds()) >= 300
    if not changed:
        return {
            "pilot_arrival_at": pilot_arrival,
            "pickup_at": prior.pickup_at,
            "delivery_at": prior.delivery_at,
            "generated_at": prior.generated_at,
            "source": prior.source,
            "confidence": prior.confidence,
            "rule_version": prior.rule_version,
            "reason": "change_below_materiality_threshold",
            "distance_m": delivery_route.distance_m,
        }
    estimate_row = await add(
        session,
        model,
        task_id=task.id,
        generated_at=instant,
        pickup_at=pickup_at,
        delivery_at=delivery_at,
        source=delivery_route.source,
        confidence=delivery_route.confidence,
        rule_version="eta-v1",
        reason="route_or_assignment_changed",
    )
    return {
        "pilot_arrival_at": pilot_arrival,
        "pickup_at": estimate_row.pickup_at,
        "delivery_at": estimate_row.delivery_at,
        "generated_at": estimate_row.generated_at,
        "source": estimate_row.source,
        "confidence": estimate_row.confidence,
        "rule_version": estimate_row.rule_version,
        "reason": estimate_row.reason,
        "distance_m": delivery_route.distance_m,
    }
