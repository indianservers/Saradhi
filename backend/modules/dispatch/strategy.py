"""Replaceable dispatch strategy interface and deterministic initial scoring model."""

from dataclasses import dataclass
from uuid import UUID

from backend.modules.tracking.service import distance_m


@dataclass(frozen=True)
class CandidateScore:
    pilot_id: UUID
    score: float
    distance_m: float
    active_tasks: int


class DispatchStrategy:
    name = "weighted-v1"

    def score(self, pilot_id, location, branch, active_tasks, weights):
        distance = distance_m(
            branch.latitude, branch.longitude, location.latitude, location.longitude
        )
        score = (
            float(weights.get("pickup_distance", 1.0)) * distance / 1000
            + float(weights.get("workload", 5.0)) * active_tasks
        )
        return CandidateScore(pilot_id, score, distance, active_tasks)
