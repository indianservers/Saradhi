"""Low-cardinality process metrics. Scrape exposure is controlled by deployment networking."""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

registry = CollectorRegistry()
http_requests = Counter(
    "quickbuddy_http_requests_total",
    "HTTP requests completed by this API process.",
    ("method", "route", "status"),
    registry=registry,
)
http_request_duration = Histogram(
    "quickbuddy_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "route"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    registry=registry,
)
security_events = Counter(
    "quickbuddy_security_events_total",
    "Authentication, authorization, and request-throttle outcomes.",
    ("event",),
    registry=registry,
)
websocket_connections = Gauge(
    "quickbuddy_websocket_connections",
    "Currently active WebSocket connections in this API process.",
    registry=registry,
)
database_pool_connections = Gauge(
    "quickbuddy_database_pool_connections",
    "Current SQLAlchemy pool connection counts for this API process.",
    ("state",),
    registry=registry,
)


def render_metrics(pool):
    database_pool_connections.labels("checked_out").set(pool.checkedout())
    database_pool_connections.labels("pool_size").set(pool.size())
    database_pool_connections.labels("overflow").set(pool.overflow())
    return generate_latest(registry), CONTENT_TYPE_LATEST
