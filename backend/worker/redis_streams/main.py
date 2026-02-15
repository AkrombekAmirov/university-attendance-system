# backend/worker/redis_streams/main.py

import asyncio
import threading
import redis
import redis.asyncio as aioredis

from backend.domain.turniked.services import TurnikedService
from backend.worker.redis_streams.manager import RedisStreamsManager
from backend.worker.redis_streams.producer import TurniketProducer
from backend.worker.redis_streams.consumer import StreamConsumer
from backend.worker.redis_streams.recovery import recovery_worker
from backend.worker.redis_streams.config import *
from backend.worker.tasks.limit_event_fetcher import EventFetcher


# 🔑 GLOBAL STATUS QUEUE (ASYNC)
status_queue: asyncio.Queue = asyncio.Queue()


async def status_worker(service: TurnikedService):
    """
    Threadlardan kelgan status update'larni async DB ga yozadi.
    """
    while True:
        device_id, status = await status_queue.get()
        try:
            await service.device_repo.set_status(device_id, status)
            print(f"📊 STATUS UPDATED → {device_id} = {status}")
        except Exception as e:
            print(f"❌ STATUS WORKER ERROR: {e}")
        finally:
            status_queue.task_done()


async def main():
    redis_async = await aioredis.from_url(REDIS_URL)
    redis_sync = redis.Redis.from_url(REDIS_URL)

    mgr = RedisStreamsManager(redis_async)
    await mgr.init()

    service = TurnikedService()
    devices = await service.get_active_devices()

    # Consumers (ASYNC)
    for i in range(NUM_WORKERS):
        asyncio.create_task(StreamConsumer(i, mgr, service).run())

    # Recovery
    asyncio.create_task(recovery_worker(mgr))

    # 🔑 STATUS WORKER
    asyncio.create_task(status_worker(service))

    # Producers (THREAD)
    for d in devices:
        fetcher = EventFetcher(d.ip_address, d.username, d.password)

        threading.Thread(
            target=TurniketProducer(
                d,
                redis_sync,
                fetcher,
                status_queue  # 🔑 async queue uzatiladi
            ).run,
            daemon=True,
        ).start()

    print("✅ TURNIKET REDIS STREAMS ENGINE STARTED")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
