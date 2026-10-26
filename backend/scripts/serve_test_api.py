"""Serve ONLY the dedicated local test database, for opt-in network/load tests."""

import os

import uvicorn
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from backend.api.app.main import create_app
from backend.shared.settings import Settings


def main():
    config = dotenv_values(".env")
    url = os.environ.get("TEST_DATABASE_URL") or config.get("TEST_DATABASE_URL", "")
    if not url or "REPLACE_ME" in url:
        raise SystemExit("Configure TEST_DATABASE_URL")
    parsed = make_url(url)
    if parsed.database != "quickbuddy_test" or parsed.host not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit("Refusing any database other than local quickbuddy_test")
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=url,
        auth_private_key_path=".secrets/integration-test-private.pem",
        auth_rate_limit_per_minute=10000,
    )
    uvicorn.run(create_app(settings), host="127.0.0.1", port=8001, access_log=False)


if __name__ == "__main__":
    main()
