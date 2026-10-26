"""Feature records include event and availability time to prevent target leakage."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

FEATURE_SCHEMA_VERSION = "quickbuddy-operational-v1"


@dataclass(frozen=True)
class FeatureValue:
    name: str
    value: Any
    event_at: datetime
    available_at: datetime
    source: str
    transformation: str
    missing_policy: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_point_in_time(features: list[FeatureValue], prediction_at: datetime) -> None:
    """Reject features that were not available at the prediction cutoff."""
    for feature in features:
        if feature.event_at > prediction_at or feature.available_at > prediction_at:
            raise ValueError(f"future_feature:{feature.name}")


def quality_summary(features: list[FeatureValue]) -> dict[str, Any]:
    missing = [f.name for f in features if f.value is None]
    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_count": len(features),
        "missing_count": len(missing),
        "missing_features": missing,
        "point_in_time_validated": True,
    }
