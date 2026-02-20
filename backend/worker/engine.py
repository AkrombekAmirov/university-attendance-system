# backend/worker/engine.py
import asyncio
import threading
from asyncio import Queue, QueueFull
from typing import List, Tuple, Optional
from datetime import datetime
from collections import deque
import time
from uuid import UUID

from requests.exceptions import ConnectionError, Timeout

from backend.domain.turniked.services import TurnikedService
from backend.worker.tasks.limit_event_fetcher import EventFetcher
# backend/worker/static_devices.py

from dataclasses import dataclass
from uuid import UUID, uuid4

@dataclass
class StaticDevice:
    id: UUID
    name: str
    ip_address: str
    username: str
    password: str


# 🔐 STATIK TURNIKETLAR
STATIC_DEVICES = [
    StaticDevice(
        id="a9f01b0d-9a18-423f-a5f1-96bda3e24da5",
        name="TTJ oqtepa-2",
        ip_address="10.39.33.67:9182",
        username="admin",
        password="abcd2024",
    )
]


# ─────────────────────────────
# CONFIG
# ─────────────────────────────
QUEUE_MAXSIZE = 10_000
NUM_DB_WORKERS = 5

# 🔑 STATIC DATE FOR ALL DEVICES
HISTORY_START_DATE = datetime(2026, 2, 1)

DB_BATCH_SIZE = 50
DB_BATCH_TIMEOUT = 0.2
QUEUE_BACKPRESSURE_SLEEP = 0.01

# ─────────────────────────────
# GLOBAL QUEUES
# ─────────────────────────────
event_queue: Queue[Tuple[dict, UUID]] = Queue(maxsize=QUEUE_MAXSIZE)
device_state_queue: Queue[Tuple[UUID, str, dict | None]] = Queue()

# ─────────────────────────────
# UTILS
# ─────────────────────────────
def parse_event_time(evt: dict) -> Optional[datetime]:
    raw = evt.get("time")
    if not raw:
        return None
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


# ─────────────────────────────
# 🔑 BINARY SEARCH BY DATE
# ─────────────────────────────
def find_start_serial_by_date(
    client: EventFetcher,
    device_name: str,
    start_date: datetime,
) -> int:
    total = client.get_total_events()
    if total <= 0:
        return 0

    low, high = 0, total - 1
    result = total

    while low <= high:
        mid = (low + high) // 2
        evt = None

        for batch in client.paged_fetch_event_range(mid, mid + 1, device_name):
            if batch:
                evt = batch[0]
                break

        if not evt:
            low = mid + 1
            continue

        evt_time = parse_event_time(evt)
        if not evt_time or evt_time < start_date:
            low = mid + 1
        else:
            result = mid
            high = mid - 1

    return max(0, result)


# ─────────────────────────────
# DEVICE STATE
# ─────────────────────────────
async def update_device_checkpoint(service: TurnikedService, device_id: UUID, last_event: dict):
    serial = last_event.get("serialNo")
    evt_time = parse_event_time(last_event)
    if serial and evt_time:
        pass
        # await service.update_device_sync_status(device_id, serial, evt_time)


async def device_state_worker(service: TurnikedService):
    while True:
        device_id, state, last_event = await device_state_queue.get()
        try:
            if state == "online":
                # await service.device_repo.mark_online(device_id)
                if last_event:
                    pass
                    # await update_device_checkpoint(service, device_id, last_event)
            else:
                pass
                # await service.device_repo.mark_offline(device_id)
        finally:
            device_state_queue.task_done()


# ─────────────────────────────
# DB WORKERS
# ─────────────────────────────
async def flush_batch(service: TurnikedService, batch: List[Tuple[dict, UUID]]):
    last_event_per_device = {}
    for event, device_id in batch:
        await service.process_realtime_event(event, device_id)
        last_event_per_device[device_id] = event

    for device_id, evt in last_event_per_device.items():
        await device_state_queue.put((device_id, "online", evt))


async def db_worker(service: TurnikedService):
    buffer: List[Tuple[dict, UUID]] = []

    while True:
        try:
            item = await asyncio.wait_for(event_queue.get(), timeout=DB_BATCH_TIMEOUT)
            buffer.append(item)
            event_queue.task_done()

            if len(buffer) >= DB_BATCH_SIZE:
                await flush_batch(service, buffer)
                buffer.clear()

        except asyncio.TimeoutError:
            if buffer:
                await flush_batch(service, buffer)
                buffer.clear()


async def safe_task(factory, name: str):
    while True:
        try:
            await factory()
        except Exception as e:
            print(f"🔥 TASK CRASHED [{name}]: {e}")
            await asyncio.sleep(1)


# ─────────────────────────────
# DEVICE THREAD
# ─────────────────────────────
def device_thread(device):
    client = EventFetcher(
        device.ip_address,
        device.username,
        device.password,
    )

    seen_serials = deque(maxlen=20_000)

    def safe_push(evt):
        while True:
            try:
                event_queue.put_nowait((evt, device.id))
                return
            except QueueFull:
                time.sleep(QUEUE_BACKPRESSURE_SLEEP)

    try:
        device_state_queue.put_nowait((device.id, "online", None))

        total = client.get_total_events()
        start = find_start_serial_by_date(client, device.name, HISTORY_START_DATE)

        for batch in client.paged_fetch_event_range(start, total, device.name):
            for evt in batch:
                serial = evt.get("serialNo")
                if not serial or serial in seen_serials:
                    continue
                seen_serials.append(serial)
                safe_push(evt)
                print(evt)

        print(f"✅ HISTORY SYNC DONE [{device.name}]")

    except (ConnectionError, Timeout) as e:
        device_state_queue.put_nowait((device.id, "offline", None))
        print(f"🔴 DEVICE OFFLINE [{device.name}]: {e}")
        raise


def device_supervisor(device):
    while True:
        try:
            print(f"🟢 START DEVICE [{device.name}]")
            device_thread(device)
            break
        except Exception as e:
            print(f"🔥 DEVICE CRASH [{device.name}]: {e}")
            time.sleep(2)


# ─────────────────────────────
# MAIN
# ─────────────────────────────
async def main():
    service = TurnikedService()
    devices = STATIC_DEVICES

    if not devices:
        print("⚠️ NO STATIC DEVICES")
        return

    for _ in range(NUM_DB_WORKERS):
        asyncio.create_task(safe_task(lambda: db_worker(service), "db_worker"))

    asyncio.create_task(
        safe_task(lambda: device_state_worker(service), "device_state_worker")
    )

    for device in devices:
        threading.Thread(
            target=device_supervisor,
            args=(device,),
            daemon=True,
        ).start()

    print("✅ TURNIKET ENGINE STARTED (STATIC IP MODE)")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
