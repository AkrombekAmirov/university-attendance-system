# backend/worker/adapters/turniked_batch_adapter.py

import asyncio
from datetime import datetime
from uuid import UUID

class TurnikedBatchAdapter:
    def __init__(self, service, concurrency: int = 25):
        self.service = service
        self.sem = asyncio.Semaphore(concurrency)

    async def _one(self, event: dict, device_id: UUID):
        async with self.sem:
            await self.service.process_realtime_event(event, device_id)
            await self._update_device_checkpoint(event, device_id)

    async def _update_device_checkpoint(self, event: dict, device_id: UUID):
        raw_time = event.get("time")
        if not raw_time:
            return

        dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)

        # 🔑 last_serial_no = OFFSET
        await self.service.update_device_sync_status(
            device_id=device_id,
            last_serial_no=None,      # consumer OFFSETni bilmaydi
            last_event_time=dt,
        )

    async def process_batch(self, events):
        if not events:
            return

        await asyncio.gather(
            *[self._one(evt, did) for evt, did in events]
        )
