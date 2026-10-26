import time
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from backend.shared.auth import OIDCVerifier
from backend.shared.settings import Settings


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
