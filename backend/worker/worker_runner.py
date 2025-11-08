# test_runner.py (yoki __main__.py da sinov)
import asyncio
from backend.worker.tasks.limit_event_fetcher import LimitedEventFetcher

async def main():
    fetcher = LimitedEventFetcher(
        ip="192.128.1.211",
        username="admin",
        password="abcd2024",
        device_id="f90e14dc-8176-4f08-b222-ccab7bca3f44",
        device_name="Turniket 1",
        serial_limit=1000
    )
    await fetcher.run()

if __name__ == "__main__":
    asyncio.run(main())
