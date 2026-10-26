"""Stable IDs and honest lifecycle metadata for built-in rule baselines."""

from dataclasses import dataclass
from uuid import UUID, uuid5

NAMESPACE = UUID("14e57ad0-467c-4f88-a4e8-515a6c2a6b54")


@dataclass(frozen=True)
class BaselineSpec:
    key: str
    name: str
    algorithm: str
    version: str = "v1"
    status: str = "deterministic"

    @property
    def model_id(self) -> UUID:
        return uuid5(NAMESPACE, "ai-baseline:" + self.key)

    @property
    def version_id(self) -> UUID:
        return uuid5(NAMESPACE, "ai-baseline-version:" + self.key + ":" + self.version)


BASELINES = {
    spec.key: spec
    for spec in (
        BaselineSpec("demand", "quickbuddy-demand-baseline", "seasonal_naive_v1"),
        BaselineSpec("preparation", "quickbuddy-preparation-baseline", "queue_item_rule_v1"),
        BaselineSpec("eta", "quickbuddy-eta-baseline", "road_duration_rule_v1"),
        BaselineSpec("dispatch", "quickbuddy-dispatch-baseline", "weighted_score_v1"),
        BaselineSpec("risk", "quickbuddy-risk-baseline", "operational_rules_v1"),
        BaselineSpec("recommendations", "quickbuddy-recommendations-baseline", "popularity_v1"),
    )
}
