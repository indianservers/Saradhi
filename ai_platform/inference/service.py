"""PostgreSQL-backed feature extraction and explicit deterministic inference logging."""

import hashlib
import json
from datetime import UTC, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import distinct, func, select

from ai_platform.evaluations.demand import error_metrics, time_split_backtest
from ai_platform.features.contracts import FEATURE_SCHEMA_VERSION, FeatureValue, quality_summary
from ai_platform.models.demand.baseline import forecast_hourly
from ai_platform.registry.baselines import BASELINES
from backend.application.common import add, now
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F


async def city_order_features(session, city, cutoff, days=28, zone_id=None):
    """Extract hourly order counts available by cutoff, grouped in city-local time."""
    local_hour = func.date_trunc("hour", func.timezone(city.timezone, m.Order.created_at))
    cutoff_local = cutoff.astimezone(ZoneInfo(city.timezone))
    hour_boundary_utc = cutoff_local.replace(minute=0, second=0, microsecond=0).astimezone(UTC)
    query = (
        select(local_hour, func.count(distinct(m.Order.id)))
        .join(m.MerchantOrder, m.MerchantOrder.order_id == m.Order.id)
        .join(m.Branch, m.Branch.id == m.MerchantOrder.branch_id)
        .where(
            m.Branch.city_id == city.id,
            m.Order.created_at < hour_boundary_utc,
            m.Order.created_at >= cutoff - timedelta(days=days),
            m.Order.status.not_in(["cancelled", "rejected"]),
        )
        .group_by(local_hour)
        .order_by(local_hour)
    )
    if zone_id:
        area = m.ServiceArea
        query = (
            query.join(m.BranchArea, m.BranchArea.branch_id == m.Branch.id)
            .join(area, area.id == m.BranchArea.area_id)
            .where(area.zone_id == zone_id)
        )
    rows = (await session.execute(query)).all()
    observed = {timestamp: int(count) for timestamp, count in rows}
    upper = cutoff_local.replace(minute=0, second=0, microsecond=0)
    lower = upper - timedelta(days=days)
    features = []
    cursor = lower
    while cursor < upper:
        local_naive = cursor.replace(tzinfo=None)
        available_at = cursor + timedelta(hours=1)
        features.append(
            FeatureValue(
                name="city_orders_hourly",
                value=observed.get(local_naive, 0),
                event_at=available_at,
                available_at=available_at,
                source="commerce.orders.created_at",
                transformation="distinct_order_count_by_city_local_hour_v1",
                missing_policy="zero_for_unobserved_hour",
            )
        )
        cursor += timedelta(hours=1)
    quality = quality_summary(features)
    quality.update(
        {
            "source_rows": len(rows),
            "nonzero_order_hours": sum(1 for count in observed.values() if count),
            "lookback_days": days,
            "pii_excluded": True,
        }
    )
    return features, quality, cutoff_local


async def city_demand_forecast(session, city, cutoff=None, zone_id=None):
    cutoff = cutoff or now()
    features, quality, local_cutoff = await city_order_features(
        session, city, cutoff, zone_id=zone_id
    )
    history = []
    for row in features:
        history.append((row.event_at, row.value))
    hourly = forecast_hourly(history, local_cutoff, 24)
    horizons = {
        "next_30_minutes": round(hourly[0]["expected_orders"] * 0.5, 3),
        "next_1_hour": round(sum(x["expected_orders"] for x in hourly[:1]), 3),
        "next_4_hours": round(sum(x["expected_orders"] for x in hourly[:4]), 3),
        "next_24_hours": round(sum(x["expected_orders"] for x in hourly), 3),
    }
    return {
        "city_id": str(city.id),
        "zone_id": str(zone_id) if zone_id else None,
        "generated_at": cutoff.isoformat(),
        "source_cutoff": cutoff.isoformat(),
        "timezone": city.timezone,
        "provenance": "deterministic_rule",
        "model_status": "untrained_baseline" if quality["source_rows"] else "cold_start_fallback",
        "model_version": "demand-v1",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "sample_count": quality["source_rows"],
        "horizons": horizons,
        "hourly": hourly,
        "data_quality": quality,
    }


async def demand_backtest(session, city, cutoff=None):
    cutoff = cutoff or now()
    features, quality, _ = await city_order_features(session, city, cutoff)
    observations = [(feature.event_at, feature.value) for feature in features]
    result = (
        time_split_backtest(observations)
        if quality["source_rows"]
        else {
            "sample_count": 0,
            "reason": "no_historical_orders",
            "metrics": error_metrics([], []),
        }
    )
    result.update(
        {"city_id": str(city.id), "source_cutoff": cutoff.isoformat(), "quality": quality}
    )
    return result


async def log_prediction(
    session, key, actor_id, prediction_type, payload, output, organization_id=None
):
    """Store redacted digest + prediction through the existing intelligence ledger."""
    version_id = BASELINES[key].version_id
    input_digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    run_model = F["intelligence.ai_inference_runs"]
    run = await add(
        session,
        run_model,
        version_id=version_id,
        actor_id=UUID(str(actor_id)),
        organization_id=organization_id,
        input_digest=input_digest,
        status="succeeded",
        retention_until=now() + timedelta(days=7),
    )
    await add(
        session,
        F["intelligence.ai_prediction_records"],
        run_id=run.id,
        prediction_type=prediction_type,
        output=json.loads(json.dumps(output, default=str)),
        expires_at=now() + timedelta(days=7),
    )
    return run.id


def preparation_rule(item_count: int, queue_depth: int):
    """Transparent cold-start estimate; not a trained kitchen preparation model."""
    minutes = min(120, max(8, 12 + 2 * item_count + 4 * queue_depth))
    return {
        "expected_duration_minutes": minutes,
        "earliest_ready_minutes": minutes,
        "uncertainty_interval_minutes": None,
        "confidence": None,
        "provenance": "deterministic_rule",
        "model_status": "untrained_baseline",
        "model_version": "preparation-v1",
        "rule": "12 minutes + 2 minutes/item + 4 minutes/queued order; capped at 120",
    }
