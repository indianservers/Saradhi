import time
from types import SimpleNamespace
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from starlette.requests import Request

from backend.api.v1.routes import local_auth
from backend.domain.rules import BusinessError
from backend.shared.auth import OIDCVerifier
from backend.shared.settings import Settings


def production_settings(**overrides):
    values = {
        "_env_file": None,
        "app_env": "production",
        "database_url": "postgresql+asyncpg://quickbuddy:strong-password@db.example/quickbuddy",
        "database_ssl": True,
        "cors_origins": ["https://admin.quickbuddy.example"],
        "oidc_issuer": "https://identity.quickbuddy.example",
        "oidc_audience": "quickbuddy-api",
        "oidc_jwks_url": "https://identity.quickbuddy.example/.well-known/jwks.json",
    }
    return Settings(**(values | overrides))


def test_production_rejects_local_password_signing_key():
    with pytest.raises(ValueError, match="Local password authentication is forbidden"):
        production_settings(auth_private_key_path="/run/secrets/local-auth.pem")


def test_production_accepts_oidc_without_local_password_auth():
    assert production_settings().app_env == "production"


def test_staging_requires_remote_tls_and_oidc_configuration():
    values = {
        "app_env": "staging",
        "database_url": "postgresql+asyncpg://staging:injected@db.example/quickbuddy_staging",
        "database_ssl": True,
        "cors_origins": ["https://staging-admin.quickbuddy.example"],
        "oidc_issuer": "https://staging-identity.quickbuddy.example",
        "oidc_audience": "quickbuddy-staging",
        "oidc_jwks_url": "https://staging-identity.quickbuddy.example/.well-known/jwks.json",
    }
    settings = production_settings(**values)
    assert settings.app_env == "staging"
    with pytest.raises(ValueError, match="verified TLS"):
        production_settings(**(values | {"database_ssl": False}))


def test_local_registration_guard_rejects_oidc_verifier():
    app = SimpleNamespace(state=SimpleNamespace(token_verifier=object()))
    request = Request({"type": "http", "app": app})
    with pytest.raises(BusinessError, match="Configure AUTH_PRIVATE_KEY_PATH"):
        local_auth(request)


@pytest.fixture
def signed_identity():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = int(time.time())
    claims = dict(
        sub="user-123",
        iss="https://id.example",
        aud="quickbuddy",
        exp=now + 60,
        iat=now,
        roles=["support_agent"],
    )
    verifier = OIDCVerifier(
        Settings(
            _env_file=None,
            oidc_issuer="https://id.example",
            oidc_audience="quickbuddy",
            oidc_jwks_url="https://id.example/jwks",
        )
    )
    return key, claims, verifier


@pytest.mark.parametrize("change", [{}, {"aud": "other"}, {"exp": 1}, {"roles": "company_admin"}])
async def test_signed_token_validation(signed_identity, change):
    key, claims, verifier = signed_identity
    claims.update(change)
    token = jwt.encode(claims, key, algorithm="RS256")

    class SigningKey:
        pass

    result = SigningKey()
    result.key = key.public_key()
    with patch.object(verifier.jwks, "get_signing_key_from_jwt", return_value=result):
        if change:
            with pytest.raises(HTTPException) as error:
                await verifier.verify(token)
            assert error.value.status_code == 401
        else:
            principal = await verifier.verify(token)
            assert principal.subject == "user-123"
            assert principal.roles == frozenset({"support_agent"})
