from types import SimpleNamespace

from fastapi import Request
from fastapi.testclient import TestClient

from backend.api.app.main import create_app
from backend.shared.client_ip import client_ip
from backend.shared.settings import Settings


def test_forwarded_ip_is_ignored_without_a_trusted_proxy():
    app = SimpleNamespace(state=SimpleNamespace(settings=Settings(_env_file=None)))
    request = SimpleNamespace(
        app=app,
        client=SimpleNamespace(host="192.0.2.10"),
        headers={"x-forwarded-for": "198.51.100.99"},
    )
    assert client_ip(request) == "192.0.2.10"


def test_forwarded_ip_uses_only_a_configured_proxy_chain():
    app = SimpleNamespace(
        state=SimpleNamespace(settings=Settings(_env_file=None, trusted_proxy_cidrs=["10.0.0.0/8"]))
    )
    request = SimpleNamespace(
        app=app,
        client=SimpleNamespace(host="10.1.2.3"),
        headers={"x-forwarded-for": "198.51.100.9, 10.2.3.4"},
    )
    assert client_ip(request) == "198.51.100.9"


def test_request_body_limit_rejects_oversized_payload_before_auth_or_database():
    settings = Settings(_env_file=None, app_env="test", max_request_body_bytes=1024)
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/auth/login",
            content=b"x" * 1025,
            headers={"content-type": "application/json"},
        )
        get_response = client.request("GET", "/api/v1/roles", content=b"x" * 1025)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"
    assert get_response.status_code == 413


def test_invalid_forwarded_chain_falls_back_to_proxy_peer():
    app = SimpleNamespace(
        state=SimpleNamespace(settings=Settings(_env_file=None, trusted_proxy_cidrs=["10.0.0.0/8"]))
    )
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(b"x-forwarded-for", b"not-an-ip")],
            "client": ("10.1.2.3", 1234),
            "server": ("test", 80),
            "app": app,
        }
    )
    assert client_ip(request) == "10.1.2.3"
