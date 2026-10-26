"""Bounded local-date recurrence expansion; reject ambiguous/nonexistent wall times."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.domain.rules import BusinessError


def resolve_wall_time(day: date, wall_time: time, timezone: str):
    naive = datetime.combine(day, wall_time.replace(tzinfo=None))
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise BusinessError("schedule_timezone", "Use a valid IANA time zone", 422) from exc
    instants = set()
    for fold in (0, 1):
        candidate = naive.replace(tzinfo=zone, fold=fold).astimezone(UTC)
        if candidate.astimezone(zone).replace(tzinfo=None) == naive:
            instants.add(candidate)
    if len(instants) != 1:
        raise BusinessError(
            "schedule_dst_review",
            "Local time is ambiguous or nonexistent; choose an explicit replacement",
            422,
        )
    return next(iter(instants))


def occurrences(anchor, start, end, wall_time, timezone, frequency, interval, exceptions):
    if end < start or (end - start).days > 90 or interval < 1:
        raise BusinessError(
            "schedule_range", "Expand at most 90 days with a positive interval", 422
        )
    if frequency not in {"daily", "weekly", "monthly", "business_days"}:
        raise BusinessError("schedule_frequency", "Unsupported recurrence frequency", 422)
    result = []
    day = max(anchor, start)
    while day <= end:
        elapsed = (day - anchor).days
        months = (day.year - anchor.year) * 12 + day.month - anchor.month
        weeks, remainder = divmod(elapsed, 7)
        business_elapsed = weeks * 5 + sum(
            (anchor + timedelta(days=i)).weekday() < 5 for i in range(remainder)
        )
        matches = (
            frequency == "daily"
            and elapsed % interval == 0
            or frequency == "weekly"
            and day.weekday() == anchor.weekday()
            and (elapsed // 7) % interval == 0
            or frequency == "monthly"
            and day.day == anchor.day
            and months % interval == 0
            or frequency == "business_days"
            and day.weekday() < 5
            and business_elapsed % interval == 0
        )
        if matches and day not in exceptions:
            result.append(resolve_wall_time(day, wall_time, timezone))
        day += timedelta(days=1)
    # A monthly day absent from a month is skipped, never silently clamped to a different date.
    return result
