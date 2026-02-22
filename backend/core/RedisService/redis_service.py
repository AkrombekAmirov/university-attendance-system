import asyncio
import json
import time
import threading
from typing import List, Tuple, Dict
from datetime import datetime
from uuid import UUID
from collections import deque

import redis
import redis.asyncio as aioredis
from redis.exceptions import ResponseError

from backend.domain.turniked.services import TurnikedService
from backend.worker.tasks.limit_event_fetcher import EventFetcher

REDIS_URL = "redis://redis:6379/1"


STREAM_RT = "turniket:rt"
STREAM_HIST = "turniket:hist"
STREAM_DLQ = "turniket:dlq"

GROUP_RT = "cg-rt"
GROUP_HIST = "cg-hist"

DEDUP_KEY = "turniket:dedup"
DEDUP_TTL = 86400  # 1 day

NUM_WORKERS = 15
BATCH_SIZE = 300
BLOCK_MS = 2000

MAX_RETRIES = 3
CLAIM_IDLE_MS = 60_000

# ─────────────────────────────────────────
# REDIS STREAMS MANAGER
# ─────────────────────────────────────────
class RedisStreamsManager:
    def __init__(self, redis_async):
        self.redis = redis_async

    async def init(self):
        for stream, group in [(STREAM_RT, GROUP_RT), (STREAM_HIST, GROUP_HIST)]:
            try:
                await self.redis.xgroup_create(stream, group, id="0", mkstream=True)
            except ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

    async def xadd(self, stream: str, data: dict):
        await self.redis.xadd(stream, data, maxlen=1_000_000, approximate=True)

    async def read(self, stream, group, consumer, count):
        res = await self.redis.xreadgroup(
            group, consumer, {stream: ">"}, count=count, block=BLOCK_MS
        )
        if not res:
            return []
        return [(msg_id.decode(), msg) for msg_id, msg in res[0][1]]

    async def ack(self, stream, group, *ids):
        if ids:
            await self.redis.xack(stream, group, *ids)

    async def claim(self, stream, group, consumer):
        res = await self.redis.execute_command(
            "XAUTOCLAIM",
            stream, group, consumer, CLAIM_IDLE_MS, "0-0", "COUNT", 100
        )
        return [(msg_id.decode(), msg) for msg_id, msg in res[1]] if res else []

# ─────────────────────────────────────────
# PRODUCER (DEVICE THREAD)
# ─────────────────────────────────────────
class TurniketProducer:
    def __init__(self, device, redis_sync: redis.Redis):
        self.device = device
        self.client = EventFetcher(
            device.ip_address, device.username, device.password
        )
        self.redis = redis_sync
        self.seen = deque(maxlen=50_000)

    def dedup(self, serial: str) -> bool:
        key = f"{DEDUP_KEY}:{self.device.id}:{serial}"
        return self.redis.set(key, 1, nx=True, ex=DEDUP_TTL)

    def push(self, evt: dict):
        serial = evt.get("serialNo")
        if not serial or not self.dedup(serial):
            return

        payload = {
            "device_id": str(self.device.id),
            "event": json.dumps(evt),
            "retry": "0",
            "ts": str(time.time())
        }
        self.redis.xadd(STREAM_RT, payload, maxlen=1_000_000, approximate=True)

    def run(self):
        last = self.client.get_total_events()
        while True:
            try:
                total = self.client.get_total_events()
                if total > last:
                    for batch in self.client.paged_fetch_event_range(last, total, self.device.name):
                        for evt in batch:
                            self.push(evt)
                    last = total
            except Exception:
                time.sleep(2)
            time.sleep(0.1)

# ─────────────────────────────────────────
# CONSUMER WORKER
# ─────────────────────────────────────────
class StreamConsumer:
    def __init__(self, wid: int, mgr: RedisStreamsManager, service: TurnikedService):
        self.consumer = f"worker-{wid}"
        self.mgr = mgr
        self.service = service

    async def run(self):
        while True:
            rt = await self.mgr.read(STREAM_RT, GROUP_RT, self.consumer, BATCH_SIZE)
            hist = []
            if len(rt) < BATCH_SIZE:
                hist = await self.mgr.read(
                    STREAM_HIST, GROUP_HIST, self.consumer, BATCH_SIZE - len(rt)
                )

            msgs = rt + hist
            if not msgs:
                await asyncio.sleep(0.5)
                continue

            events = []
            ack_rt, ack_hist = [], []

            for mid, data in msgs:
                try:
                    evt = json.loads(data[b"event"])
                    did = UUID(data[b"device_id"].decode())
                    events.append((evt, did))
                    (ack_rt if (mid in dict(rt)) else ack_hist).append(mid)
                except:
                    continue

            try:
                await self.service.process_realtime_event(events)
                await self.mgr.ack(STREAM_RT, GROUP_RT, *ack_rt)
                await self.mgr.ack(STREAM_HIST, GROUP_HIST, *ack_hist)
            except Exception:
                await asyncio.sleep(1)