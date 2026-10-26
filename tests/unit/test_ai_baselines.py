from datetime import UTC, datetime, timedelta

import pytest

from ai_platform.features.contracts import FeatureValue, validate_point_in_time
from ai_platform.models.demand.baseline import error_metrics, forecast_hourly, time_split_backtest
from ai_platform.optimization.dispatch.greedy import greedy_one_to_one


def test_forecast_cold_start_and_future_observation_exclusion():
    start = datetime(2026, 10, 1, tzinfo=UTC)
    history = [
        (start - timedelta(days=7) + timedelta(hours=1), 3),
        (start + timedelta(hours=1), 100),
    ]
    forecast = forecast_hourly(history, start, 1)
    assert forecast[0]["expected_orders"] == 3
    assert forecast[0]["sample_count"] == 1
    assert forecast_hourly([], start, 1)[0]["baseline"] == "cold_start_zero"


def test_feature_contract_rejects_late_available_feature():
    cutoff = datetime(2026, 10, 1, tzinfo=UTC)
    feature = FeatureValue(
        "orders",
        2,
        cutoff - timedelta(hours=1),
        cutoff + timedelta(seconds=1),
        "commerce.orders",
        "hourly_count_v1",
        "zero",
    )
    with pytest.raises(ValueError, match="future_feature:orders"):
        validate_point_in_time([feature], cutoff)


def test_backtest_is_time_split_and_metrics_handle_zero_actuals():
    start = datetime(2026, 1, 1, tzinfo=UTC)
    observations = [(start + timedelta(hours=i), i % 4) for i in range(30)]
    report = time_split_backtest(observations, min_train=24)
    assert report["sample_count"] == 6
    assert report["split"] == "chronological_expanding_window"
    zero = error_metrics([0, 0], [1, 0])
    assert zero["wape"] is None
    assert zero["wape_zero_demand_policy"] == "undefined_when_total_actual_is_zero"


def test_greedy_plan_respects_distinct_tasks_and_capacity():
    tasks = [{"id": "a"}, {"id": "b"}]
    pilots = [{"id": "p1", "remaining_capacity": 1}, {"id": "p2", "remaining_capacity": 1}]
    plan = greedy_one_to_one(tasks, pilots, lambda task, pilot: 1 if pilot["id"] == "p1" else 2)
    assert len(plan) == 2
    assert {item["task_id"] for item in plan} == {"a", "b"}
    assert {item["pilot_id"] for item in plan} == {"p1", "p2"}
