import asyncio
from datetime import datetime
from loguru import logger

from backend.domain.turniked.services import TurnikedService
from backend.core.LoggingService import logger as log_info


class DeviceMonitorWorker:
    def init(self, service: TurnikedService, device):
        self.service = service
        self.device = device
        self.device_name = device.name
        self.device_ip = device.ip
        self.device_id = device.id
        self._is_active = True

    async def get_latest_serial_and_time(self) -> tuple[int, datetime]:
        """
        Simulatsiya qilingan qurilmadan so‘nggi serial va vaqtni olish.
        Real qurilmada bu GET API orqali olinadi.
        """
        now = datetime.utcnow()
        serial = int(now.timestamp())  # Simulated serial
        return serial, now

    async def run(self):
        log_info(f"📡 [{self.device_name}] Real‑time monitoring started.")
        try:
            while self._is_active:
                serial, timestamp = await self.get_latest_serial_and_time()
                await self.service.update_device_sync_status(
                    device_id=self.device_id,
                    last_serial_no=serial,
                    last_event_time=timestamp
                )
                logger.info(f"✅ [{self.device_name}] Serial: {serial}, Time: {timestamp.isoformat()}")
                await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"❌ Device {self.device_name} crashed: {e}")
            await self.service.mark_device_offline(self.device_ip)

    def stop(self):
        self._is_active = False