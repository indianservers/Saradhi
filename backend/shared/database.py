import ssl
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.shared.settings import Settings


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def create_database(settings: Settings):
    args = {
        "server_settings": {
            "timezone": "UTC",
            "statement_timeout": "10000",
            "lock_timeout": "5000",
            "idle_in_transaction_session_timeout": "30000",
        },
        "timeout": 3,
        "command_timeout": 15,
    }
    if settings.database_ssl:
        args["ssl"] = ssl.create_default_context()
    return create_async_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=5,
        pool_recycle=1800,
        connect_args=args,
    )


@asynccontextmanager
async def session_scope(factory: async_sessionmaker) -> AsyncIterator[AsyncSession]:
    async with factory() as session, session.begin():
        yield session
