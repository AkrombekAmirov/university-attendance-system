from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from backend.domain.turniked.models import (
    Device,
    AttendanceEvent,
    DailyAttendance,
    MonthlyAttendanceSummary,
)
from backend.core.DatabaseService.base import DatabaseService
from backend.domain.turniked.turniked_repo import (
    DeviceRepository,
    AttendanceEventRepository,
    DailyAttendanceRepository,
    MonthlyAttendanceRepository
)


class TurnikedService:
    """
    Turniked (turniket) moduli uchun barcha biznes logika shu servis qatlamida jamlangan.
    Har bir model uchun tegishli repository orqali ma'lumotlar bazasi bilan ishlaydi.
    """

    def __init__(self, db: Optional[DatabaseService] = None):
        self.db = db or DatabaseService()
        self.device_repo = DeviceRepository(self.db)
        self.event_repo = AttendanceEventRepository(self.db)
        self.daily_repo = DailyAttendanceRepository(self.db)
        self.monthly_repo = MonthlyAttendanceRepository(self.db)

    # ===================== DEVICE =====================
    async def process_realtime_event(self, event: dict, device_id: UUID):
        # if event["datetime"].tzinfo:
        #     event["datetime"] = event["datetime"].replace(tzinfo=None)
        return await self.event_repo.process_event(event, device_id)

    async def create_device(self, device: Device) -> Device:
        """Yangi qurilma qo‘shish."""
        return await self.device_repo.create(device)

    async def mark_device_online(self, device_id: UUID):
        return await self.device_repo.mark_online(device_id)

    async def mark_device_offline(self, device_ip: str):
        return await self.device_repo.mark_offline(device_ip)

    async def get_device_by_id(self, device_ip: str) -> Optional[Device]:
        """ID bo‘yicha qurilma topish."""
        return await self.device_repo.get_by_id(device_ip)

    async def get_device_by_ip(self, ip: str) -> Optional[Device]:
        """IP manzili orqali qurilma olish."""
        return await self.device_repo.get_by_ip(ip)

    async def get_active_devices(self) -> List[Device]:
        """Faol holatdagi barcha qurilmalar."""
        return await self.device_repo.get_active_devices()

    async def update_device_sync_status(self, device_id: UUID, last_serial_no: int, last_event_time: datetime) -> \
            Optional[UUID]:
        """
        Qurilmaning sinxronlash holatini yangilash:
        - Qurilma so‘nggi yuborgan `serial_no` va `event_time` ni saqlash.
        """
        return await self.device_repo.update_sync_status(
            device_id=device_id,
            last_serial_no=last_serial_no,
            last_event_time=last_event_time,
        )

    # ===================== EVENT =====================

    async def create_event(self, event: AttendanceEvent) -> AttendanceEvent:
        """Yangi turniket event qo‘shish."""
        return await self.event_repo.create(event)

    async def get_events_by_person_on_date(self, person_id: UUID, day: date) -> List[AttendanceEvent]:
        """Berilgan kunda bir kishining eventlari."""
        return await self.event_repo.get_by_person_on_date(person_id, day)

    async def get_events_between_dates(self, person_id: UUID, start_date: date, end_date: date) -> List[
        AttendanceEvent]:
        """Berilgan foydalanuvchining oraliqdagi eventlari."""
        return await self.event_repo.get_between_dates(person_id, start_date, end_date)

    async def get_latest_event_by_device(self, device_id: UUID) -> Optional[AttendanceEvent]:
        """Qurilma bo‘yicha eng so‘nggi eventni olish."""
        return await self.event_repo.get_latest_by_device(device_id)

    # ===================== DAILY ATTENDANCE =====================
    async def upsert_daily_attendance(
            self,
            person_id: UUID,
            org_unit_id: UUID,
            date_: date,
            updates: dict
    ) -> DailyAttendance:
        """Kunlik ishtirokni yangilash yoki yaratish."""
        return await self.daily_repo.upsert_daily(
            person_id=person_id,
            org_unit_id=org_unit_id,
            date_=date_,
            updates=updates,
        )

    async def get_daily_by_person_and_date(self, person_id: UUID, day: date) -> Optional[DailyAttendance]:
        """Kundalik ishtirokni olish."""
        return await self.daily_repo.get_by_person_and_date(person_id, day)

    # ===================== MONTHLY ATTENDANCE =====================
    async def upsert_monthly_attendance(
            self,
            person_id: UUID,
            org_unit_id: UUID,
            year: int,
            month: int,
            updates: dict
    ) -> MonthlyAttendanceSummary:
        """Oylik ishtirokni yangilash yoki yaratish."""
        return await self.monthly_repo.upsert_monthly(
            person_id=person_id,
            org_unit_id=org_unit_id,
            year=year,
            month=month,
            updates=updates,
        )

    async def get_monthly_by_person(self, person_id: UUID, year: int, month: int) -> Optional[MonthlyAttendanceSummary]:
        """Oylik ishtirokni olish."""
        return await self.monthly_repo.get_by_person_and_month(person_id, year, month)

    # TurnikedService ichida

    async def save_raw_event(self, session, evt: dict):
        """
        Atomic insert of turniket event:
        - ignore duplicates
        - push day/month aggregations later (background)
        """
        event_hash = f"{evt['device_id']}|{evt['serial']}"

        exists = await self.event_repo.get_by_event_hash(session, event_hash)
        if exists:
            return

        model = AttendanceEvent(
            device_id=evt["device_id"],
            user_id=evt["user_id"],
            direction=evt["direction"],
            hash_code=event_hash,
            event_date=evt["event_date"],
            event_time=evt["event_time"].time(),
            extra_data=evt.get("raw")
        )

        session.add(model)
