# Phase 12.C test accounts and data

No named, reusable, public, or default admin account was created. No passwords, tokens, or personal test identities are stored in this report.

The integration fixture in `tests/integration/conftest.py` uses only loopback `quickbuddy_test`, refuses any other DB, applies Alembic migrations, and creates an ignored `.secrets/integration-test-private.pem` when needed. `tests/integration/helpers.py` generates unique synthetic emails/passwords for each test. Test records persist in the isolated test DB; the fixture does not reset it. The development DB had zero role assignments at audit time.

The requested broad seeded topology (two countries, three cities, two unrelated merchants, multiple pilots, corporate account, etc.) was **not** established as one reproducible test world. Individual tests create the fixtures they need with unique identifiers. Do not treat accumulated synthetic rows as a curated reusable account set.

To run safely: configure `TEST_DATABASE_URL` for local `quickbuddy_test` only, then run `.venv\Scripts\python.exe -m pytest tests/integration -q`. Never copy generated credentials to development/production or commit `.secrets`.
