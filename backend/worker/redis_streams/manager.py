# backend/worker/redis_streams/manager.py

from redis.exceptions import ResponseError
from backend.worker.redis_streams.config import *

class RedisStreamsManager:
    def __init__(self, redis_async):
        self.redis = redis_async

    async def init(self):
        for stream, group in [
            (REDIS_STREAM_RT, REDIS_GROUP_RT),
            (REDIS_STREAM_HIST, REDIS_GROUP_HIST),
        ]:
            try:
                await self.redis.xgroup_create(stream, group, id="0", mkstream=True)
            except ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

    async def read(self, stream, group, consumer, count):
        res = await self.redis.xreadgroup(
            group,
            consumer,
            {stream: ">"},
            count=count,
            block=REDIS_STREAM_BLOCK_MS,
        )
        if not res:
            return []
        return [(mid.decode(), data) for mid, data in res[0][1]]

    async def ack(self, stream, group, *ids):
        if ids:
            await self.redis.xack(stream, group, *ids)

    async def claim(self, stream, group, consumer):
        res = await self.redis.execute_command(
            "XAUTOCLAIM",
            stream,
            group,
            consumer,
            REDIS_STREAM_CLAIM_IDLE_MS,
            "0-0",
            "COUNT",
            100,
        )
        return [(mid.decode(), data) for mid, data in res[1]] if res else []
