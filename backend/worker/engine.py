import asyncio, traceback
from warnings import catch_warnings

from backend.domain.turniked.services import TurnikedService
# from backend.worker.tasks.single_turniket_runner import TurniketClient
# from backend.worker.tasks.sync_events import event_worker
from backend.worker.tasks.limit_event_fetcher import EventFetcher
from asyncio import Queue
import asyncio


event_queue = Queue()
NUM_WORKERS = 5

async def event_worker():
    service = TurnikedService()
    while True:
        try:
            event, device_id = await event_queue.get()
            print(event, '📥 QABUL QILINDI')
            await service.process_realtime_event(event, device_id)
        except Exception as e:
            print(f"❌ Worker error: {e}")
        finally:
            event_queue.task_done()

async def monitor_device(device):
    client = EventFetcher(device.ip_address, device.username, device.password)
    loop = asyncio.get_running_loop()

    def blocking_fetch():
        try:
            total = client.get_total_events()
            start = max(0, total - 1000)
            for batch in client.paged_fetch_event_range(start, total):
                for evt in batch:
                    asyncio.run_coroutine_threadsafe(
                        event_queue.put((evt, device.id)), loop
                    )
        except Exception as e:
            print(f"❌ Fetch error from {device.name}: {e}")

    await asyncio.to_thread(blocking_fetch)

async def main():
    service = TurnikedService()
    devices = await service.get_active_devices()

    workers = [asyncio.create_task(event_worker()) for _ in range(NUM_WORKERS)]

    for d in devices:
        asyncio.create_task(monitor_device(d))

    await asyncio.Event().wait()  # never exit

if __name__ == "__main__":
    asyncio.run(main())
