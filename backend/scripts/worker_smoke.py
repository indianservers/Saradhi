import asyncio

from arq import create_pool
from arq.worker import Worker

from backend.workers.main import WorkerSettings, demonstration, startup


async def main():
    pool = await create_pool(WorkerSettings.redis_settings)
    try:
        job = await pool.enqueue_job("demonstration", _queue_name=WorkerSettings.queue_name)
        worker = Worker(
            [demonstration],
            redis_pool=pool,
            burst=True,
            queue_name=WorkerSettings.queue_name,
            on_startup=startup,
            health_check_key=WorkerSettings.health_check_key,
        )
        await worker.async_run()
        result = await job.result(timeout=5)
        assert result == {"status": "ok", "message": "foundation-check"}
        print("PASS: Redis ping, worker startup, queued demonstration, persisted result")
    finally:
        await pool.aclose()


if __name__ == "__main__":
    asyncio.run(main())
