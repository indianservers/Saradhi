import asyncio
import hashlib
import hmac
import secrets
from datetime import timedelta
from pathlib import Path
from typing import Protocol
from uuid import UUID

import jwt
from argon2.exceptions import VerificationError
from cryptography.hazmat.primitives import serialization
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.application.common import add, now, owned
from backend.domain.rules import BusinessError
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS
from backend.shared.auth import Principal, password_hasher


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class LocalTokenVerifier:
    def __init__(self, settings, sessions):
        self.settings, self.sessions = settings, sessions
        self.private = Path(settings.auth_private_key_path).read_bytes()
        key = serialization.load_pem_private_key(self.private, password=None)
        self.public = key.public_key()

    def access(self, user_id, session_id):
        instant = now()
        return jwt.encode(
            {
                "sub": str(user_id),
                "sid": str(session_id),
                "iss": self.settings.auth_issuer,
                "aud": self.settings.auth_audience,
                "iat": instant,
                "exp": instant + timedelta(seconds=self.settings.access_token_seconds),
            },
            self.private,
            algorithm="RS256",
        )

    async def verify(self, token):
        try:
            claims = jwt.decode(
                token,
                self.public,
                algorithms=["RS256"],
                issuer=self.settings.auth_issuer,
                audience=self.settings.auth_audience,
                options={"require": ["sub", "sid", "exp", "iat", "iss", "aud"]},
            )
            uid, sid = UUID(claims["sub"]), UUID(claims["sid"])
        except (jwt.PyJWTError, ValueError, KeyError) as exc:
            raise BusinessError("invalid_token", "Invalid or expired access token", 401) from exc
        async with self.sessions() as session:
            record = await session.get(m.Session, sid)
            user = await session.get(m.User, uid)
            if (
                not record
                or record.user_id != uid
                or record.revoked_at
                or record.expires_at <= now()
                or not user
                or user.status != "active"
            ):
                raise BusinessError("invalid_token", "Session is no longer valid", 401)
            roles = (
                await session.scalars(
                    select(m.Role.name)
                    .join(m.RoleAssignment)
                    .where(m.RoleAssignment.user_id == uid)
                )
            ).all()
        return Principal(str(uid), frozenset(roles))


async def rate_limit(session, identity, network, *, limit=10):
    """Durable shared PostgreSQL buckets; callers COMMIT failures too, before raising."""
    instant = now().replace(second=0, microsecond=0)
    for raw in ("identity:" + identity, "network:" + network):
        query = insert(m.RateBucket).values(
            bucket_key=digest(raw), window_start=instant, attempts=1
        )
        query = query.on_conflict_do_update(
            index_elements=["bucket_key", "window_start"],
            set_={"attempts": m.RateBucket.attempts + 1},
        ).returning(m.RateBucket.attempts)
        attempts = await session.scalar(query)
        if attempts > limit:
            return False
    return True


async def register(session, email, password):
    normalized = email.strip().lower()
    if await session.scalar(select(m.Email.id).where(m.Email.address == normalized)):
        raise BusinessError("identity_exists", "Identity already registered", 409)
    user = await add(session, m.User, status="active")
    await add(session, m.Email, user_id=user.id, address=normalized)
    hashed = await asyncio.to_thread(password_hasher.hash, password)
    await add(session, m.Credential, user_id=user.id, password_hash=hashed)
    role = await session.scalar(select(m.Role).where(m.Role.name == "customer"))
    if role:
        await add(session, m.RoleAssignment, user_id=user.id, role_id=role.id)
    profile = FOUNDATION_MODELS["identity.customer_profiles"]
    await add(session, profile, user_id=user.id, preferred_currency="INR")
    return user


async def issue(session, verifier, user_id, session_record=None):
    expires = now() + timedelta(days=verifier.settings.refresh_token_days)
    if session_record is None:
        session_record = await add(session, m.Session, user_id=user_id, expires_at=expires)
    raw = secrets.token_urlsafe(48)
    await add(
        session,
        m.RefreshToken,
        session_id=session_record.id,
        digest=digest(raw),
        expires_at=expires,
    )
    return {
        "access_token": verifier.access(user_id, session_record.id),
        "refresh_token": raw,
        "token_type": "bearer",
        "expires_in": verifier.settings.access_token_seconds,
    }


async def login(session, verifier, email, password):
    user = await session.scalar(
        select(m.User).join(m.Email).where(m.Email.address == email.strip().lower())
    )
    credential = (
        await session.scalar(select(m.Credential).where(m.Credential.user_id == user.id))
        if user
        else None
    )
    # Hash even an unknown account to reduce identity timing leakage; never log credentials.
    if not credential:
        await asyncio.to_thread(password_hasher.hash, password)
        return None
    try:
        await asyncio.to_thread(password_hasher.verify, credential.password_hash, password)
    except VerificationError:
        return None
    if user.status != "active":
        return None
    if password_hasher.check_needs_rehash(credential.password_hash):
        credential.password_hash = await asyncio.to_thread(password_hasher.hash, password)
    return await issue(session, verifier, user.id)


async def refresh(session, verifier, raw):
    token = await session.scalar(
        select(m.RefreshToken).where(m.RefreshToken.digest == digest(raw)).with_for_update()
    )
    if token is None:
        return None
    record = await session.scalar(
        select(m.Session).where(m.Session.id == token.session_id).with_for_update()
    )
    if token.used_at is not None:
        # Caller commits this security revocation even though the refresh will return 401.
        record.revoked_at = now()
        return None
    if record.revoked_at or record.expires_at <= now() or token.expires_at <= now():
        return None
    user = await session.get(m.User, record.user_id)
    if not user or user.status != "active":
        return None
    token.used_at = now()
    return await issue(session, verifier, record.user_id, record)


class OTPProvider(Protocol):
    async def send(self, destination_reference: str, otp: str) -> None: ...


async def create_challenge(
    session, user_id, purpose, destination, pepper, provider: OTPProvider | None
):
    if provider is None or len(pepper) < 32:
        raise BusinessError("otp_unconfigured", "OTP provider and pepper are required", 503)
    # Lock identity: serializes resend attempts across replicas.
    await session.scalar(select(m.User).where(m.User.id == user_id).with_for_update())
    recent = await session.scalar(
        select(m.Challenge.id).where(
            m.Challenge.user_id == user_id, m.Challenge.created_at > now() - timedelta(seconds=60)
        )
    )
    if recent:
        raise BusinessError("otp_throttled", "Wait before requesting another code", 429)
    raw = f"{secrets.randbelow(1_000_000):06d}"
    challenge = await add(
        session,
        m.Challenge,
        user_id=user_id,
        purpose=purpose,
        destination_reference=destination,
        digest=hmac.new(pepper.encode(), raw.encode(), "sha256").hexdigest(),
        expires_at=now() + timedelta(minutes=5),
        attempts=0,
    )
    # Provider sends only when configured; provider failure rolls back challenge.
    await provider.send(destination, raw)
    return challenge


async def consume_challenge(session, actor, challenge_id, code, pepper):
    challenge = await session.scalar(
        select(m.Challenge).where(m.Challenge.id == challenge_id).with_for_update()
    )
    if not challenge:
        return False
    owned(actor, challenge.user_id)
    if challenge.consumed_at or challenge.expires_at <= now() or challenge.attempts >= 5:
        return False
    challenge.attempts += 1
    valid = hmac.compare_digest(
        challenge.digest, hmac.new(pepper.encode(), code.encode(), "sha256").hexdigest()
    )
    if valid:
        challenge.consumed_at = now()
        if challenge.purpose == "verify_email":
            email = await session.scalar(
                select(m.Email).where(
                    m.Email.user_id == challenge.user_id,
                    m.Email.address == challenge.destination_reference,
                )
            )
            if email:
                email.verified_at = now()
    return valid
