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

# ─────────────────────────────
# CONFIG
# ─────────────────────────────
QUEUE_MAXSIZE = 10_000
NUM_DB_WORKERS = 5

# 🔑 STATIC DATE FOR ALL DEVICES
HISTORY_START_DATE = datetime(2026, 2, 18, 0, 0, 0)

DB_BATCH_SIZE = 50
DB_BATCH_TIMEOUT = 0.2

QUEUE_BACKPRESSURE_SLEEP = 0.01  # 🔒 queue to‘lib qolsa kutish

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

    if dt.tzinfo:
        dt = dt.astimezone().replace(tzinfo=None)

    return dt


# ─────────────────────────────
# 🔑 CORE: BINARY SEARCH BY DATE
# ─────────────────────────────
def find_start_serial_by_date(
    client: EventFetcher,
    device_name: str,
    start_date: datetime,
) -> int:
    total = client.get_total_events()
    if total <= 0:
        return 0

    low = 0
    high = total - 1
    result = total

    print(f"🔍 [{device_name}] BINARY SEARCH START (total={total})")

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
        print(
            f"🔎 [{device_name}] CHECK serial={evt.get('serialNo')} "
            f"time={evt_time}"
        )

        if not evt_time:
            low = mid + 1
            continue

        if evt_time < start_date:
            low = mid + 1
        else:
            result = mid
            high = mid - 1

    print(f"🎯 [{device_name}] START SERIAL FOUND = {result}")
    return max(0, result)


# ─────────────────────────────
# DEVICE CHECKPOINT UPDATE
# ─────────────────────────────
async def update_device_checkpoint(
    service: TurnikedService,
    device_id: UUID,
    last_event: dict,
):
    serial = last_event.get("serialNo")
    evt_time = parse_event_time(last_event)
    if not serial or not evt_time:
        return

    # await service.update_device_sync_status(
    #     device_id=device_id,
    #     last_serial_no=serial,
    #     last_event_time=evt_time,
    # )


# ─────────────────────────────
# DEVICE STATE WORKER
# ─────────────────────────────
async def device_state_worker(service: TurnikedService):
    while True:
        device_id, state, last_event = await device_state_queue.get()
        try:
            if state == "online":
                pass
                # await service.device_repo.mark_online(device_id)
                if last_event:
                    pass
                    # await update_device_checkpoint(service, device_id, last_event)
            elif state == "offline":
                pass
                # await service.device_repo.mark_offline(device_id)
        finally:
            device_state_queue.task_done()


# ─────────────────────────────
# DB BATCH FLUSH
# ─────────────────────────────
async def flush_batch(service: TurnikedService, batch: List[Tuple[dict, UUID]]):
    last_event_per_device = {}

    for event, device_id in batch:
        await service.process_realtime_event(event, device_id)
        last_event_per_device[device_id] = event

    for device_id, evt in last_event_per_device.items():
        await device_state_queue.put((device_id, "online", evt))


# ─────────────────────────────
# DB WORKER
# ─────────────────────────────
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


# ─────────────────────────────
# SAFE TASK
# ─────────────────────────────
async def safe_task(factory, name: str):
    while True:
        try:
            await factory()
        except Exception as e:
            print(f"🔥 TASK CRASHED [{name}]: {e}")
            await asyncio.sleep(1)


# ─────────────────────────────
# DEVICE THREAD (DATE-BASED HISTORY)
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
                print(f"⏳ QUEUE FULL → WAIT [{device.name}]")
                time.sleep(QUEUE_BACKPRESSURE_SLEEP)

    try:
        device_state_queue.put_nowait((device.id, "online", None))

        total = client.get_total_events()

        start = find_start_serial_by_date(
            client,
            device.name,
            HISTORY_START_DATE,
        )

        print(
            f"📅 [{device.name}] HISTORY FROM {HISTORY_START_DATE.date()} "
            f"(serial={start} → {total})"
        )

        for batch in client.paged_fetch_event_range(start, total, device.name):
            for evt in batch:
                serial = evt.get("serialNo")
                if not serial or serial in seen_serials:
                    continue

                seen_serials.append(serial)

                # 🔍 PRINT EVERY EVENT
                print(
                    f"📜 [{device.name}] "
                    f"serial={serial} time={parse_event_time(evt)}"
                )

                safe_push(evt)

        print(f"✅ HISTORY SYNC COMPLETED [{device.name}]")

    except (ConnectionError, Timeout) as e:
        device_state_queue.put_nowait((device.id, "offline", None))
        print(f"🔴 OFFLINE [{device.name}]: {e}")
        raise


# ─────────────────────────────
# DEVICE SUPERVISOR
# ─────────────────────────────
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
    devices = await service.get_active_devices()

    if not devices:
        print("⚠️ NO ACTIVE DEVICES")
        return

    for _ in range(NUM_DB_WORKERS):
        asyncio.create_task(
            safe_task(lambda: db_worker(service), "db_worker")
        )

    asyncio.create_task(
        safe_task(lambda: device_state_worker(service), "device_state_worker")
    )

    for device in devices:
        threading.Thread(
            target=device_supervisor,
            args=(device,),
            daemon=True,
        ).start()

    print("✅ TURNIKET ENGINE STARTED (BINARY DATE HISTORY MODE)")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
