"""Redis-backed demo worker only. Not an order/payment workflow engine."""

from arq.connections import RedisSettings

from backend.shared.logging import configure_logging
from backend.shared.settings import get_settings


async def demonstration(ctx, message: str = "foundation-check") -> dict[str, str]:
    return {"status": "ok", "message": message}


async def startup(ctx):
    configure_logging()
    await ctx["redis"].ping()


class WorkerSettings:
    functions = [demonstration]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url.get_secret_value())
    queue_name = "quickbuddy:demo"
    health_check_key = "quickbuddy:worker:health"
    health_check_interval = 10
    max_jobs = 5
    max_tries = 3
    job_timeout = 30
