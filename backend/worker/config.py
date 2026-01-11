# backend/worker/engine.py
import asyncio
import threading
import time
from asyncio import Queue, QueueFull
from typing import List, Tuple
from datetime import datetime
from collections import deque

from requests.exceptions import ConnectionError, Timeout

from backend.domain.turniked.services import TurnikedService
from backend.worker.tasks.limit_event_fetcher import EventFetcher

# ─────────────────────────────
# CONFIG
# ─────────────────────────────
QUEUE_MAXSIZE = 10_000
NUM_DB_WORKERS = 5

HISTORY_LIMIT = 500
REALTIME_INTERVAL = 0.2
REALTIME_WINDOW = 100

DB_BATCH_SIZE = 50
DB_BATCH_TIMEOUT = 0.2

# ─────────────────────────────
# 🔥 STATIC TURNIKET CONFIG (MANUAL TEST)
# ─────────────────────────────
STATIC_TURNIKETS = [
    {
        "id": "a9f01b0d-9a18-423f-a5f1-96bda3e22ac1",
        "name": "9-TTJ-1",
        "ip": "10.130.156.2",
        "port": 9187,
        "username": "admin",
        "password": "12345",
    },
    {
        "id": "a9f01b0d-9a18-423f-a5f1-96bda3e22ab3",
        "name": "10-TTJ-2",
        "ip": "10.130.156.2",
        "port": 9187,
        "username": "admin",
        "password": "admin123",
    },
]

# ─────────────────────────────
# GLOBAL QUEUES
# ─────────────────────────────
event_queue: Queue[Tuple[dict, str]] = Queue(maxsize=QUEUE_MAXSIZE)
device_state_queue: Queue[Tuple[str, str, dict | None]] = Queue()

# ─────────────────────────────
# DEVICE CHECKPOINT UPDATE
# ─────────────────────────────
async def update_device_checkpoint(service, device_id, last_event):
    serial = last_event.get("serialNo")
    raw_time = last_event.get("time")
    if not serial or not raw_time:
        return

    dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)

    await service.update_device_sync_status(
        device_id=device_id,
        last_serial_no=serial,
        last_event_time=dt,
    )

# ─────────────────────────────
# DEVICE STATE WORKER
# ─────────────────────────────
async def device_state_worker(service):
    while True:
        device_id, state, last_event = await device_state_queue.get()
        try:
            if state == "online":
                await service.device_repo.mark_online(device_id)
                if last_event:
                    await update_device_checkpoint(service, device_id, last_event)
            elif state == "offline":
                await service.device_repo.mark_offline(device_id)
        finally:
            device_state_queue.task_done()

# ─────────────────────────────
# DB BATCH FLUSH
# ─────────────────────────────
async def flush_batch(service, batch):
    last_event_per_device = {}
    for event, device_id in batch:
        await service.process_realtime_event(event, device_id)
        last_event_per_device[device_id] = event
        print(f"🗄️ DB WRITE device={device_id} serial={event.get('serialNo')}")

    for device_id, evt in last_event_per_device.items():
        await device_state_queue.put((device_id, "online", evt))

# ─────────────────────────────
# DB WORKER
# ─────────────────────────────
async def db_worker(service):
    buffer = []
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
# DEVICE THREAD (STATIC IP)
# ─────────────────────────────
def device_thread(cfg):
    service = TurnikedService()

    client = EventFetcher(
        f"{cfg['ip']}:{cfg['port']}",
        cfg["username"],
        cfg["password"],
    )

    seen_serials = deque(maxlen=REALTIME_WINDOW * 2)

    def safe_push(evt):
        try:
            event_queue.put_nowait((evt, cfg["id"]))
            print(f"📥 QUEUE device={cfg['name']} serial={evt.get('serialNo')}")
        except QueueFull:
            print(f"⚠️ QUEUE FULL → DROPPED device={cfg['name']}")

    try:
        device_state_queue.put_nowait((cfg["id"], "online", None))
        total = client.get_total_events()
        start = max(0, total - HISTORY_LIMIT)
        print(f"🚀 [{cfg['name']}] SYNC {start} → {total}")

        last_position = total
        for batch in client.paged_fetch_event_range(start, total, cfg["name"]):
            for evt in batch:
                serial = evt.get("serialNo")
                if not serial or serial in seen_serials:
                    continue
                seen_serials.append(serial)
                safe_push(evt)

        print(f"🔥 [{cfg['name']}] REAL-TIME STARTED")

    except Exception as e:
        device_state_queue.put_nowait((cfg["id"], "offline", None))
        print(f"🔴 [{cfg['name']}] START ERROR:", e)
        raise

    while True:
        try:
            new_total = client.get_total_events()
            if new_total > last_position:
                for batch in client.paged_fetch_event_range(last_position, new_total, cfg["name"]):
                    for evt in batch:
                        serial = evt.get("serialNo")
                        if not serial or serial in seen_serials:
                            continue
                        seen_serials.append(serial)
                        safe_push(evt)
                last_position = new_total
        except Exception as e:
            device_state_queue.put_nowait((cfg["id"], "offline", None))
            print(f"🔴 [{cfg['name']}] CONNECTION LOST:", e)
            raise
        time.sleep(REALTIME_INTERVAL)

# ─────────────────────────────
# DEVICE SUPERVISOR
# ─────────────────────────────
def device_supervisor(cfg):
    while True:
        try:
            print(f"🟢 START DEVICE [{cfg['name']}]")
            device_thread(cfg)
        except Exception as e:
            print(f"🔥 DEVICE CRASH [{cfg['name']}]: {e}")
            time.sleep(2)

# ─────────────────────────────
# MAIN
# ─────────────────────────────
async def main():
    service = TurnikedService()

    for _ in range(NUM_DB_WORKERS):
        asyncio.create_task(db_worker(service))

    asyncio.create_task(device_state_worker(service))

    for cfg in STATIC_TURNIKETS:
        threading.Thread(
            target=device_supervisor,
            args=(cfg,),
            daemon=True
        ).start()

    print("✅ TURNIKET ENGINE STARTED (STATIC IP TEST MODE)")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
