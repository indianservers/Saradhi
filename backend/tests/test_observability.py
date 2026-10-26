from fastapi.testclient import TestClient

from backend.api.app.main import create_app
from backend.shared.settings import Settings


def test_metrics_endpoint_is_disabled_by_default():
    app = create_app(Settings(_env_file=None))
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 404


def test_metrics_report_route_templates_without_request_identifiers():
    app = create_app(Settings(_env_file=None, metrics_enabled=True))
    with TestClient(app) as client:
        assert client.get("/health/live?customer=private-id").status_code == 200
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "quickbuddy_http_requests_total" in response.text
    assert 'route="/health/live"' in response.text
    assert "private-id" not in response.text
    assert response.headers["content-type"].startswith("text/plain; version=")
