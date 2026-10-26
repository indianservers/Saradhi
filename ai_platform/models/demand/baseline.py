"""Small-data demand forecasting baselines with explicit zero-history behavior."""

from collections import defaultdict
from datetime import datetime, timedelta
from math import sqrt


def forecast_hourly(history: list[tuple[datetime, int]], start: datetime, hours: int) -> list[dict]:
    """Average same local weekday/hour observations; zero is an honest cold start."""
    buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
    for timestamp, count in history:
        if timestamp <= start:
            buckets[(timestamp.weekday(), timestamp.hour)].append(int(count))
    result = []
    for offset in range(hours):
        point = start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=offset + 1)
        samples = buckets.get((point.weekday(), point.hour), [])
        value = sum(samples) / len(samples) if samples else 0.0
        result.append(
            {
                "at": point.isoformat(),
                "expected_orders": round(value, 3),
                "baseline": "same_weekday_hour_mean" if samples else "cold_start_zero",
                "sample_count": len(samples),
            }
        )
    return result


def interval_forecast(hourly: list[dict], interval_minutes: int) -> dict:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes_must_be_positive")
    fraction = interval_minutes / 60
    expected = sum(row["expected_orders"] for row in hourly) * fraction
    counts = sum(row["sample_count"] for row in hourly)
    return {
        "interval_minutes": interval_minutes,
        "expected_orders": round(expected, 3),
        "sample_count": counts,
        "method": "seasonal_naive_mean",
        "status": "baseline_untrained" if counts else "cold_start_fallback",
    }


def error_metrics(actual: list[float], predicted: list[float]) -> dict:
    if len(actual) != len(predicted):
        raise ValueError("metric_series_length_mismatch")
    if not actual:
        return {"sample_count": 0, "mae": None, "rmse": None, "wape": None, "bias": None}
    errors = [p - a for a, p in zip(actual, predicted, strict=True)]
    absolute = [abs(error) for error in errors]
    denominator = sum(abs(value) for value in actual)
    return {
        "sample_count": len(actual),
        "mae": sum(absolute) / len(actual),
        "rmse": sqrt(sum(error * error for error in errors) / len(errors)),
        "wape": sum(absolute) / denominator if denominator else None,
        "bias": sum(errors) / len(errors),
        "wape_zero_demand_policy": "undefined_when_total_actual_is_zero",
    }


def time_split_backtest(observations: list[tuple[datetime, int]], min_train: int = 24) -> dict:
    """Chronological one-step rolling backtest. Never trains on future observations."""
    ordered = sorted(observations, key=lambda row: row[0])
    if len(ordered) <= min_train:
        return {
            "sample_count": 0,
            "reason": "insufficient_history",
            "metrics": error_metrics([], []),
        }
    actual, predicted = [], []
    for index in range(min_train, len(ordered)):
        timestamp, target = ordered[index]
        prior = [
            count for prior_time, count in ordered[:index] if prior_time.hour == timestamp.hour
        ]
        estimate = sum(prior[-4:]) / len(prior[-4:]) if prior else 0.0
        actual.append(float(target))
        predicted.append(estimate)
    return {
        "sample_count": len(actual),
        "split": "chronological_expanding_window",
        "metrics": error_metrics(actual, predicted),
    }
