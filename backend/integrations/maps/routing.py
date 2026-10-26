"""Routing interface; all durations must be road/network results from a configured provider."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RouteResult:
    distance_m: int
    duration_seconds: int
    source: str
    confidence: str
    geometry: str | None = None


class RoutingProvider(Protocol):
    async def route(
        self, origin: tuple[float, float], destination: tuple[float, float]
    ) -> RouteResult: ...
    async def distance_matrix(
        self, points: list[tuple[float, float]]
    ) -> list[list[RouteResult]]: ...
    async def optimize_multi_stop(self, points: list[tuple[float, float]]) -> list[int]: ...


class RoutingUnavailable(RuntimeError):
    pass


class UnavailableRoutingProvider:
    async def route(self, origin, destination):
        raise RoutingUnavailable("No licensed road-routing provider is configured")

    async def distance_matrix(self, points):
        raise RoutingUnavailable("No licensed road-routing provider is configured")

    async def optimize_multi_stop(self, points):
        raise RoutingUnavailable("No licensed road-routing provider is configured")


class FixtureRoutingProvider:
    """Deterministic route fixture for tests; never enabled in a deployed app."""

    source = "test_fixture"
    confidence = "fixture"

    async def route(self, origin, destination):
        # Explicit deterministic fixture; does not pretend that Euclidean distance is a road.
        key = (tuple(origin), tuple(destination))
        result = self.routes.get(key)
        if result is None:
            raise RoutingUnavailable("No deterministic route fixture matches these coordinates")
        return result

    def __init__(self, routes):
        self.routes = routes

    async def distance_matrix(self, points):
        return [[await self.route(a, b) for b in points] for a in points]

    async def optimize_multi_stop(self, points):
        if not points:
            return []
        remaining = set(range(1, len(points)))
        path = [0]
        while remaining:
            current = points[path[-1]]
            next_index = min(
                remaining,
                key=lambda index: (
                    self.routes[(tuple(current), tuple(points[index]))].duration_seconds
                ),
            )
            path.append(next_index)
            remaining.remove(next_index)
        return path
