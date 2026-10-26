import asyncio
from dataclasses import dataclass
from typing import Annotated, Protocol

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from backend.shared.settings import Settings

# Argon2id defaults; rehash after login when parameters change. No password endpoints in Phase 1.
password_hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str]


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> Principal: ...


class OIDCVerifier:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.jwks = (
            PyJWKClient(settings.oidc_jwks_url, timeout=5) if settings.oidc_jwks_url else None
        )

    async def verify(self, token: str) -> Principal:
        if not self.jwks:
            raise HTTPException(503, "Authentication provider is not configured")
        try:
            key = await asyncio.to_thread(self.jwks.get_signing_key_from_jwt, token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                issuer=self.settings.oidc_issuer,
                audience=self.settings.oidc_audience,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
            roles = claims.get("roles", [])
            if not isinstance(claims["sub"], str) or not claims["sub"]:
                raise ValueError("Invalid subject")
            if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
                raise ValueError("Invalid roles")
            return Principal(claims["sub"], frozenset(roles))
        except (jwt.PyJWTError, ValueError) as exc:
            raise HTTPException(401, "Invalid or expired access token") from exc


async def current_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            401, "Bearer access token required", headers={"WWW-Authenticate": "Bearer"}
        )
    return await request.app.state.token_verifier.verify(credentials.credentials)


def authorize(principal: Principal, role: str) -> None:
    if role not in principal.roles:
        raise HTTPException(403, "Insufficient permission")


class OwnershipPolicy(Protocol):
    async def can_access(self, principal: Principal, resource_id: str, action: str) -> bool: ...
