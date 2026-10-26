"""Redis-backed demo worker only. Not an order/payment workflow engine."""

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.application import events, logistics, maintenance, recurring
from backend.integrations.realtime.redis_publisher import RedisEventPublisher
from backend.shared.database import create_database
from backend.shared.logging import configure_logging
from backend.shared.settings import get_settings


async def demonstration(ctx, message: str = "foundation-check") -> dict[str, str]:
    return {"status": "ok", "message": message}


async def startup(ctx):
    configure_logging()
    await ctx["redis"].ping()
    settings = get_settings()
    ctx["database_engine"] = create_database(settings)
    ctx["sessions"] = async_sessionmaker(ctx["database_engine"], expire_on_commit=False)


async def shutdown(ctx):
    engine = ctx.get("database_engine")
    if engine:
        await engine.dispose()


async def relay_outbox(ctx):
    return await events.relay_batch(ctx["sessions"], RedisEventPublisher(ctx["redis"]))


async def expire_dispatch_offers(ctx):
    async with ctx["sessions"].begin() as session:
        return await logistics.expire_offers(session)


async def run_bounded_maintenance(ctx):
    async with ctx["sessions"].begin() as session:
        expired = await maintenance.expire_reservations(session, limit=100)
        pruned = await maintenance.prune_ephemeral(session, limit=1000)
        return {"expired_reservations": expired, "pruned": pruned}


async def expand_recurring_schedules(ctx):
    async with ctx["sessions"].begin() as session:
        return await recurring.expand_active_plans(session, limit=100, horizon_days=14)


class WorkerSettings:
    functions = [
        demonstration,
        relay_outbox,
        expire_dispatch_offers,
        run_bounded_maintenance,
        expand_recurring_schedules,
    ]
    cron_jobs = [
        cron(relay_outbox, second=set(range(60)), run_at_startup=True),
        cron(expire_dispatch_offers, second=set(range(0, 60, 5)), run_at_startup=True),
        cron(run_bounded_maintenance, second={0}, run_at_startup=True),
        cron(expand_recurring_schedules, minute={0, 15, 30, 45}, run_at_startup=True),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url.get_secret_value())
    queue_name = "quickbuddy:demo"
    health_check_key = "quickbuddy:worker:health"
    health_check_interval = 10
    max_jobs = 5
    max_tries = 3
    job_timeout = 30
