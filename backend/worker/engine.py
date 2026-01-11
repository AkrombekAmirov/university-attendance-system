# backend/worker/engine.py
import asyncio
import threading
from asyncio import Queue
from typing import List, Tuple
from datetime import datetime

from requests.exceptions import ConnectionError, Timeout

from backend.domain.turniked.services import TurnikedService
from backend.worker.tasks.limit_event_fetcher import EventFetcher

# ─────────────────────────────
# CONFIG
# ─────────────────────────────
QUEUE_MAXSIZE = 10_000
NUM_DB_WORKERS = 5

HISTORY_LIMIT = 10            # birinchi ishga tushishda
REALTIME_INTERVAL = 0.2        # realtime polling
REALTIME_WINDOW = 100          # offline → online sync oynasi

DB_BATCH_SIZE = 50
DB_BATCH_TIMEOUT = 0.2

# ─────────────────────────────
# GLOBAL QUEUES
# ─────────────────────────────
event_queue: Queue[Tuple[dict, str]] = Queue(maxsize=QUEUE_MAXSIZE)

# Device holati uchun ALOHIDA queue
# (device_id, "online" | "offline", last_event | None)
device_state_queue: Queue[Tuple[str, str, dict | None]] = Queue()

# ─────────────────────────────
# DEVICE CHECKPOINT UPDATE (DB LOOP ONLY)
# ─────────────────────────────
async def update_device_checkpoint(
    service: TurnikedService,
    device_id,
    last_event: dict,
):
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
# DEVICE STATE WORKER (ONLINE / OFFLINE)
# ─────────────────────────────
async def device_state_worker(service: TurnikedService):
    """
    Device sync_status va checkpoint'larni
    FAQAT MAIN EVENT LOOP’da yangilaydi
    """
    while True:
        device_id, state, last_event = await device_state_queue.get()
        try:
            if state == "online":
                await service.device_repo.mark_online(device_id)
                if last_event:
                    await update_device_checkpoint(service, device_id, last_event)

            elif state == "offline":
                await service.device_repo.mark_offline(device_id)

        except Exception as e:
            print("❌ Device state worker error:", e)
        finally:
            device_state_queue.task_done()

# ─────────────────────────────
# DB BATCH FLUSH
# ─────────────────────────────
async def flush_batch(service: TurnikedService, batch: List[Tuple[dict, str]]):
    last_event_per_device = {}

    for event, device_id in batch:
        await service.process_realtime_event(event, device_id)
        last_event_per_device[device_id] = event
        print(
            f"🗄️ DB WRITE device={device_id} "
            f"serial={event}"
        )

    # 🔑 batch tugagach checkpoint
    for device_id, evt in last_event_per_device.items():
        await device_state_queue.put((device_id, "online", evt))

# ─────────────────────────────
# DB WORKER (ASYNC)
# ─────────────────────────────
async def db_worker(service: TurnikedService):
    buffer: List[Tuple[dict, str]] = []

    while True:
        try:
            item = await asyncio.wait_for(
                event_queue.get(), timeout=DB_BATCH_TIMEOUT
            )
            buffer.append(item)
            event_queue.task_done()

            if len(buffer) >= DB_BATCH_SIZE:
                await flush_batch(service, buffer)
                buffer.clear()

        except asyncio.TimeoutError:
            if buffer:
                await flush_batch(service, buffer)
                buffer.clear()

        except Exception as e:
            print("❌ DB worker error:", e)

# ─────────────────────────────
# DEVICE THREAD (SYNC + REALTIME)
# ─────────────────────────────
def device_thread(device):
    """
    ❗ BU YERDA DB YO‘Q
    ❗ FAQAT EVENT FETCH + QUEUE
    """
    client = EventFetcher(device.ip_address, device.username, device.password)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def push(evt):
        await event_queue.put((evt, device.id))

    # ─────────────────────────
    # 1️⃣ OFFLINE → ONLINE SYNC
    # ─────────────────────────
    try:
        device_state_queue.put_nowait((device.id, "online", None))

        total = client.get_total_events()

        if device.last_serial_no is not None:
            start = max(0, device.last_serial_no - REALTIME_WINDOW)
            print(
                f"🔁 [{device.name}] OFFLINE SYNC "
                f"{start} → {total} (last_serial={device.last_serial_no})"
            )
        else:
            start = max(0, total - HISTORY_LIMIT)
            print(f"🚀 [{device.name}] INITIAL SYNC {start} → {total}")

        last_position = total
        seen_serials = set()

        for batch in client.paged_fetch_event_range(start, total, device.name):
            for evt in batch:
                serial = evt.get("serialNo")
                if not serial:
                    continue
                if device.last_serial_no and serial <= device.last_serial_no:
                    continue

                seen_serials.add(serial)
                loop.run_until_complete(push(evt))

        print(f"🔥 [{device.name}] REAL-TIME STARTED")

    except (ConnectionError, Timeout) as e:
        device_state_queue.put_nowait((device.id, "offline", None))
        print(f"🔴 [{device.name}] OFFLINE (startup): {e}")
        return

    # ─────────────────────────
    # 2️⃣ REAL-TIME LOOP
    # ─────────────────────────
    while True:
        try:
            new_total = client.get_total_events()

            if new_total > last_position:
                for batch in client.paged_fetch_event_range(
                    last_position, new_total, device.name
                ):
                    for evt in batch:
                        serial = evt.get("serialNo")
                        if not serial or serial in seen_serials:
                            continue

                        seen_serials.add(serial)
                        loop.run_until_complete(push(evt))

                last_position = new_total

        except (ConnectionError, Timeout):
            device_state_queue.put_nowait((device.id, "offline", None))
            print(f"🔴 [{device.name}] CONNECTION LOST")

        except Exception as e:
            print(f"❌ [{device.name}] ERROR:", e)

        loop.run_until_complete(asyncio.sleep(REALTIME_INTERVAL))

# ─────────────────────────────
# MAIN
# ─────────────────────────────
async def main():
    service = TurnikedService()
    devices = await service.get_active_devices()

    # DB workers
    for _ in range(NUM_DB_WORKERS):
        asyncio.create_task(db_worker(service))

    # Device state worker
    asyncio.create_task(device_state_worker(service))

    # Device threads
    for device in devices:
        threading.Thread(
            target=device_thread,
            args=(device,),
            daemon=True
        ).start()

    print("✅ TURNIKET ENGINE STARTED (SAFE OFFLINE SYNC + REAL-TIME)")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
