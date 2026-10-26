from datetime import date, time

import pytest

from backend.domain.rules import BusinessError
from backend.domain.scheduling import occurrences, resolve_wall_time


@pytest.mark.parametrize(
    "day,clock", [(date(2026, 3, 8), time(2, 30)), (date(2026, 11, 1), time(1, 30))]
)
def test_dst_gap_and_fold_require_review(day, clock):
    with pytest.raises(BusinessError):
        resolve_wall_time(day, clock, "America/New_York")


def test_monthly_occurrences_skip_missing_day_and_keep_timezone():
    values = occurrences(
        date(2026, 1, 31),
        date(2026, 1, 31),
        date(2026, 3, 31),
        time(8),
        "Asia/Kolkata",
        "monthly",
        1,
        set(),
    )
    assert [v.day for v in values] == [31, 31]
    assert all(v.hour == 2 and v.minute == 30 for v in values)


def test_business_days_honor_explicit_holiday_exceptions():
    values = occurrences(
        date(2026, 10, 26),
        date(2026, 10, 26),
        date(2026, 11, 1),
        time(8),
        "UTC",
        "business_days",
        1,
        {date(2026, 10, 28)},
    )
    assert len(values) == 4
