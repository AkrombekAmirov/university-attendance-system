# backend/worker/sync/device_sync_tracker.py

from datetime import datetime
from backend.domain.turniked.turniked_repo import DeviceSyncStatus

class DeviceSyncTracker:
    def __init__(self, service, device):
        self.service = service
        self.device = device

        # 🔑 DB — source of truth
        self.last_serial = device.last_serial_no
        self.last_event_time = device.last_event_time

    async def mark_syncing(self):
        await self.service.device_repo.set_status(
            self.device.id, DeviceSyncStatus.syncing
        )

    async def mark_online(self):
        await self.service.device_repo.set_status(
            self.device.id, DeviceSyncStatus.online
        )

    async def mark_offline(self):
        await self.service.device_repo.set_status(
            self.device.id, DeviceSyncStatus.offline
        )

    async def checkpoint(self, serial: int, event_time: datetime):
        """
        🔒 Har bir eventdan keyin DB ga yoziladi
        """
        self.last_serial = serial
        self.last_event_time = event_time

        await self.service.update_device_sync_status(
            device_id=self.device.id,
            last_serial_no=serial,
            last_event_time=event_time,
        )
