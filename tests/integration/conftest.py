"""Opt-in REAL PostgreSQL suite. Never resets or drops a database.

Uses only quickbuddy_test on loopback. Missing credentials => explicit skip, not fake success.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url

from backend.api.app.main import create_app
from backend.shared.settings import Settings

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def database_url():
    url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(ROOT / ".env").get(
        "TEST_DATABASE_URL"
    )
    if not url or "REPLACE_ME" in url:
        pytest.skip(
            "REAL POSTGRESQL BLOCKED: configure authorized TEST_DATABASE_URL for quickbuddy_test"
        )
    parsed = make_url(url)
    if parsed.database != "quickbuddy_test" or parsed.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Integration tests refuse any database except local quickbuddy_test")
    environment = {**os.environ, "APP_ENV": "test", "DATABASE_URL": url}
    command = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )
    if command.returncode:
        pytest.fail(
            "Real PostgreSQL migration failed. "
            "Run the guarded migration command for sanitized diagnostics."
        )
    return url


@pytest_asyncio.fixture
async def api(database_url):
    target = ROOT / ".secrets/integration-test-private.pem"
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        target.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        target.chmod(0o600)
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=database_url,
        auth_private_key_path=str(target),
        sandbox_payments_enabled=True,
        sandbox_webhook_secret="integration-only-secret-not-a-real-payment-provider",
        auth_rate_limit_per_minute=10000,
        api_requests_per_minute=100000,
        otp_pepper="integration-only-otp-pepper-not-a-live-provider-secret",
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client, app
