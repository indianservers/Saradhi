from unittest.mock import AsyncMock

import pytest

from backend.shared.database import session_scope
from backend.workers.main import demonstration, startup


class Session:
    def __init__(self):
        self.exits = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, kind, value, traceback):
        self.exits.append(kind)

    def begin(self):
        return self


async def test_session_commits_scope_on_success():
    session = Session()
    async with session_scope(lambda: session) as actual:
        assert actual is session
    assert session.exits == [None, None]


async def test_session_exception_exits_transaction_and_session():
    session = Session()
    with pytest.raises(ValueError):
        async with session_scope(lambda: session):
            raise ValueError("use case failed")
    assert session.exits == [ValueError, ValueError]


async def test_demo_function_and_startup_contract():
    redis = AsyncMock()
    await startup({"redis": redis})
    redis.ping.assert_awaited_once()
    assert await demonstration({}, "test") == {"status": "ok", "message": "test"}
    # This validates function contracts only, not a real Redis/ARQ integration.
