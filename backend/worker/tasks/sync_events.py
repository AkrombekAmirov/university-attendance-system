from backend.domain.turniked.services import TurnikedService
import asyncio

service = TurnikedService()



event_queue: asyncio.Queue = asyncio.Queue()


async def event_worker():
    while True:
        try:
            event, device_id = await event_queue.get()
            print(event, '12313213333333')
            await service.process_realtime_event(event, device_id)
        except Exception as e:
            print(f"❌ Worker error: {e}")
        finally:
            event_queue.task_done()