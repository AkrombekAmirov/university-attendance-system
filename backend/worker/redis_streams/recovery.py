# backend/worker/redis_streams/recovery.py

import asyncio
from backend.worker.redis_streams.config import *

async def recovery_worker(mgr):
    while True:
        await mgr.claim(REDIS_STREAM_RT, REDIS_GROUP_RT, "recovery")
        await asyncio.sleep(10)
