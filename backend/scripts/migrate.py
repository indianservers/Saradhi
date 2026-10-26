"""Local-only migration runner. Never creates, resets, downgrades or drops databases."""

import argparse
import os
import subprocess
import sys

from dotenv import dotenv_values
from sqlalchemy.engine import make_url


def main(test=False):
    configured = dotenv_values(".env")
    key = "TEST_DATABASE_URL" if test else "DATABASE_URL"
    url = os.environ.get(key) or configured.get(key, "")
    if not url or "REPLACE_ME" in url:
        raise SystemExit(f"BLOCKED: configure authorized {key}; no credentials attempted")
    parsed = make_url(url)
    expected = "quickbuddy_test" if test else "quickbuddy_dev"
    if parsed.database != expected or parsed.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("This command permits only the dedicated local Quickbuddy database")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": url, "APP_ENV": "test" if test else "development"},
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise SystemExit(
            "Migration failed; credentials and SQL parameters are suppressed. No reset performed."
        )
    print(f"Migrations applied successfully to {expected} on {parsed.host}:{parsed.port or 5432}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    main(parser.parse_args().test)
