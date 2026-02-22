# backend/worker/redis_streams/consumer.py

import json
import asyncio
from uuid import UUID
from backend.worker.redis_streams.config import *
from backend.worker.adapters.turniked_batch_adapter import TurnikedBatchAdapter

class StreamConsumer:
    def __init__(self, wid, mgr, service):
        self.consumer = f"worker-{wid}"
        self.mgr = mgr
        self.adapter = TurnikedBatchAdapter(service)

    async def run(self):
        while True:
            rt = await self.mgr.read(
                REDIS_STREAM_RT,
                REDIS_GROUP_RT,
                self.consumer,
                REDIS_STREAM_BATCH_SIZE,
            )

            if not rt:
                await asyncio.sleep(0.5)
                continue

            events = []
            ack_ids = []

            for mid, data in rt:
                try:
                    evt = json.loads(data[b"event"])
                    did = UUID(data[b"device_id"].decode())
                    events.append((evt, did))
                    ack_ids.append(mid)
                except Exception:
                    continue

            try:
                await self.adapter.process_batch(events)
                await self.mgr.ack(REDIS_STREAM_RT, REDIS_GROUP_RT, *ack_ids)
            except Exception:
                await asyncio.sleep(1)
