from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.api.app.main import create_app
from backend.shared.auth import Principal, authorize
from backend.shared.settings import Settings


@pytest.fixture
def client():
    with TestClient(create_app(Settings(app_env="test", _env_file=None))) as client:
        yield client


def test_liveness_does_not_depend_on_infrastructure(client):
    response = client.get("/health/live", headers={"X-Request-ID": "test-correlation"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "dependencies": {}}
    assert response.headers["X-Request-ID"] == "test-correlation"


def test_untrusted_request_id_is_replaced(client):
    response = client.get("/health/live", headers={"X-Request-ID": "sensitive/value"})
    assert response.headers["X-Request-ID"] != "sensitive/value"
    assert len(response.headers["X-Request-ID"]) == 36


def test_missing_token_denied(client):
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_auth_unconfigured_fails_closed(client):
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer invalid"}).status_code == 503


@pytest.mark.parametrize("available,code", [(True, 200), (False, 503)])
def test_readiness_reports_dependency_status(client, available, code):
    checks = {"postgresql": "ok" if available else "unavailable", "redis": "ok"}
    with patch("backend.api.app.main.dependencies_ready", AsyncMock(return_value=checks)):
        response = client.get("/health/ready")
    assert response.status_code == code
    assert response.json()["dependencies"] == checks


def test_errors_do_not_expose_input(client):
    response = client.get("/missing?secret=private")
    assert response.status_code == 404
    assert "private" not in response.text
    assert set(response.json()) == {"error"}


def test_explicit_cors(client):
    allowed = client.options(
        "/api/v1/me",
        headers={"Origin": "http://localhost:3001", "Access-Control-Request-Method": "GET"},
    )
    denied = client.options(
        "/api/v1/me",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3001"
    assert "access-control-allow-origin" not in denied.headers


def test_rbac_denies_wrong_role():
    with pytest.raises(HTTPException) as error:
        authorize(Principal("subject", frozenset({"support_agent"})), "company_admin")
    assert error.value.status_code == 403


@pytest.mark.parametrize(
    "overrides",
    [
        {"cors_origins": ["*"]},
        {"db_pool_size": 0},
        {"database_url": "postgresql+asyncpg://user:password@localhost/unrelated"},
        {"database_url": "sqlite:///other.db"},
        {"app_env": "production"},
    ],
)
def test_unsafe_configuration_rejected(overrides):
    with pytest.raises((ValidationError, ValueError)):
        Settings(_env_file=None, **overrides)


def test_openapi_is_authoritative(client):
    schema = client.get("/openapi.json").json()
    assert schema["paths"]["/api/v1/me"]["get"]["operationId"] == "get_me"
    assert schema["paths"]["/api/v1/me"]["get"]["security"] == [{"HTTPBearer": []}]
    assert "ErrorResponse" in schema["components"]["schemas"]


def test_validation_and_unhandled_errors_hide_sensitive_details(client):
    @client.app.get("/_test/validate")
    async def validated(value: int):
        return value

    @client.app.get("/_test/failure")
    async def failure():
        raise RuntimeError("sensitive diagnostic that must stay private")

    invalid = client.get("/_test/validate?value=private-input")
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"
    assert "private-input" not in invalid.text
    failed = client.get("/_test/failure")
    assert failed.status_code == 500
    assert failed.json()["error"]["code"] == "internal_error"
    assert "sensitive diagnostic" not in failed.text
    assert failed.headers["X-Request-ID"] == failed.json()["error"]["request_id"]
