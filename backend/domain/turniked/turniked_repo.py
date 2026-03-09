from __future__ import annotations
from datetime import date, datetime, time, timedelta
from typing import Optional, List, Dict
from calendar import monthrange
from cachetools import TTLCache
from sqlmodel import select
from uuid import UUID
from cachetools import TTLCache

from backend.domain.user.models import User

from backend.core.DatabaseService.base import DatabaseService
from backend.core.DatabaseService.repositories import BaseRepository
from backend.domain.organization.org_repo import OrganizationRepository
from backend.domain.turniked.models import AttendanceEvent, DailyAttendance, MonthlyAttendanceSummary, Device
from backend.domain.user.user_repo import UserRepository
from backend.core.LoggingService import logger

WORK_START = time(9, 0, 0)
WORK_END = time(18, 0, 0)
LUNCH_START = time(13, 0, 0)
LUNCH_END = time(14, 0, 0)

from enum import Enum


class DeviceSyncStatus(str, Enum):
    syncing = "syncing"
    online = "online"
    offline = "offline"


class AttendanceEventRepository(BaseRepository[AttendanceEvent]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(AttendanceEvent, db)
        self.org_repo = OrganizationRepository(db)
        self.users = UserRepository(db)
        self.device_repo = DeviceRepository(db)

        # 🟢 FIX: O(1) Memory leak prevention TTLCache
        # Agar 1 soat foydalanilmasa o'chib ketadi, maksimal hajmi eng muhimi chegaralangan
        self._user_cache = TTLCache(maxsize=10000, ttl=3600)
        self._device_cache = TTLCache(maxsize=1000, ttl=3600)
        self._org_cache = TTLCache(maxsize=10000, ttl=3600)

    async def _get_user_cached(self, turniked_id):
        cached_user = self._user_cache.get(turniked_id)
        if cached_user:
            return cached_user

        user = await self.users.get_by_user_turniked_id(turniked_id)
        if user:
            self._user_cache[turniked_id] = user

        return user

    async def _get_device_cached(self, device_id):
        cached_device = self._device_cache.get(device_id)
        if cached_device:
            return cached_device

        device = await self.device_repo.get_by_id(device_id)
        if device:
            self._device_cache[device_id] = device

        return device

    async def _get_org_cached(self, user_id):
        cached_org = self._org_cache.get(user_id)
        if cached_org:
            return cached_org

        org_unit_id = await self.org_repo.get_org_unit_by_user_id_(user_id)
        if org_unit_id:
            self._org_cache[user_id] = org_unit_id

        return org_unit_id

    async def process_event(self, event: dict, device_id: UUID):
        """
        Turniketdan kelgan IN eventni qayta ishlaydi.
        - first_entry → kun bo‘yicha ENG ERTA kelgan vaqt
        - last_exit   → kun bo‘yicha ENG OXIRGI o‘tilgan vaqt
        - worked_minutes → first_entry va last_exit orasidagi farq
        """

        # ─────────────────────────────
        # 1️⃣ Faqat shaxsga bog‘liq IN
        # ─────────────────────────────
        employee_no = event.get("employeeNoString")
        if not employee_no:
            return

        minor = int(event.get("minor", -1))
        if minor not in (75, 72):  # faqat KIRISH
            return

        # ─────────────────────────────
        # 2️⃣ Vaqtni normalizatsiya qilish
        # ─────────────────────────────
        raw_time = event.get("time")
        if isinstance(raw_time, str):
            now = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        else:
            now = raw_time

        if now.tzinfo:
            now = now.replace(tzinfo=None)

        event_date = now.date()
        event_time = now.time()

        async with self.db.session_scope() as session:

            # ─────────────────────────
            # 3️⃣ User va Device
            # ─────────────────────────
            user = await self._get_user_cached(employee_no)
            if not user:
                return

            device = await self._get_device_cached(device_id)
            if not device:
                return

            org_unit_id = await self._get_org_cached(user.id)

            # ─────────────────────────
            # 4️⃣ RAW EVENT (audit)
            # ─────────────────────────
            session.add(AttendanceEvent(
                user_id=user.id,
                device_id=device_id,
                direction="IN",
                turniked_id=employee_no,
                event_date=event_date,
                event_time=event_time,
                timecontrol=f"{event_date}|{event_time}",
                extra_data=event
            ))

            # ─────────────────────────
            # 5️⃣ DAILY (1 user + 1 day)
            # ─────────────────────────
            result = await session.execute(
                select(DailyAttendance)
                .where(
                    DailyAttendance.user_id == user.id,
                    DailyAttendance.event_date == event_date,
                    DailyAttendance.is_deleted == False
                )
                .with_for_update()
            )
            daily = result.scalars().first()

            # ─────────────────────────
            # 6️⃣ DAILY mavjud bo‘lsa
            # ─────────────────────────
            if daily:
                # 🔹 first_entry → faqat eng ertasi
                if daily.first_entry is None or now < daily.first_entry:
                    daily.first_entry = now
                    daily.first_device_id = device_id
                    daily.alert_flag = True

                # 🔹 last_exit → HAR DOIM oxirgisi
                daily.last_exit = now
                daily.last_device_id = device_id

                # 🔹 worked_minutes hisoblash
                if daily.first_entry and daily.last_exit and daily.last_exit >= daily.first_entry:
                    daily.worked_minutes = int(
                        (daily.last_exit - daily.first_entry).total_seconds() // 60
                    )

                # 🔹 kirishlar soni
                daily.entries_count = (daily.entries_count or 0) + 1

                session.add(daily)
                return

            # ─────────────────────────
            # 7️⃣ DAILY yo‘q → yaratamiz
            # ─────────────────────────
            daily = DailyAttendance(
                user_id=user.id,
                org_unit_id=org_unit_id,
                device_id=device_id,
                event_date=event_date,

                # 🔹 birinchi kelish
                first_entry=now,
                first_device_id=device_id,

                # 🔹 oxirgi chiqish (hozircha shu ham)
                last_exit=now,
                last_device_id=device_id,

                entries_count=1,
                alert_flag=True,
                worked_minutes=0,
                expected_minutes=480,
                shift_start_time=WORK_START,
                shift_end_time=WORK_END
            )
            session.add(daily)

            # ─────────────────────────
            # 8️⃣ MONTHLY (faqat mavjud bo‘lmasa)
            # ─────────────────────────
            m_res = await session.execute(
                select(MonthlyAttendanceSummary)
                .where(
                    MonthlyAttendanceSummary.user_id == user.id,
                    MonthlyAttendanceSummary.year == event_date.year,
                    MonthlyAttendanceSummary.month == event_date.month,
                    MonthlyAttendanceSummary.is_deleted == False
                )
                .with_for_update()
            )
            monthly = m_res.scalars().first()

            if not monthly:
                session.add(MonthlyAttendanceSummary(
                    user_id=user.id,
                    org_unit_id=org_unit_id,
                    year=event_date.year,
                    month=event_date.month,
                    present_days=1,
                    total_days=1,
                    total_expected_minutes=480
                ))

    async def get_by_person_on_date(self, user_id: UUID, target_date: date) -> List[AttendanceEvent]:
        return await self.list({
            "user_id": user_id,
            "event_date": target_date,
            "is_deleted": False
        })

    async def get_between_dates(self, user_id: UUID, start_date: date, end_date: date) -> List[AttendanceEvent]:
        async with self.db.session_scope() as session:
            stmt = (
                select(AttendanceEvent)
                .where(
                    AttendanceEvent.user_id == user_id,
                    AttendanceEvent.event_date >= start_date,
                    AttendanceEvent.event_date <= end_date,
                    AttendanceEvent.is_deleted == False
                )
                .order_by(AttendanceEvent.event_date, AttendanceEvent.event_time)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_latest_by_device(self, device_id: UUID) -> Optional[AttendanceEvent]:
        async with self.db.session_scope() as session:
            stmt = (
                select(AttendanceEvent)
                .where(
                    AttendanceEvent.device_id == device_id,
                    AttendanceEvent.is_deleted == False
                )
                .order_by(AttendanceEvent.event_date.desc(), AttendanceEvent.event_time.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_event_hash(self, event_hash: str) -> Optional[AttendanceEvent]:
        async with self.db.session_scope() as session:
            stmt = (
                select(AttendanceEvent)
                .where(
                    AttendanceEvent.hash_code == event_hash,
                    AttendanceEvent.is_deleted == False
                )
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


# ========================= DAILY ATTENDANCE ========================= #

class DailyAttendanceRepository(BaseRepository[DailyAttendance]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(DailyAttendance, db)

    async def list_by_users_and_month(
            self,
            user_ids: list[UUID],
            year: int,
            month: int
    ) -> list[DailyAttendance]:
        async with self.db.session_scope() as session:
            first_day = date(year, month, 1)
            last_day = date(year, month, monthrange(year, month)[1])

            stmt = (
                select(DailyAttendance)
                .where(
                    DailyAttendance.user_id.in_(user_ids),
                    DailyAttendance.event_date >= first_day,
                    DailyAttendance.event_date <= last_day,
                    DailyAttendance.is_deleted == False
                )
                .order_by(
                    DailyAttendance.user_id,
                    DailyAttendance.event_date.asc()
                )
            )
            res = await session.execute(stmt)
            return res.scalars().all()

    async def list_by_users_and_date(
            self,
            user_ids: list[UUID],
            day: date
    ) -> list[DailyAttendance]:
        async with self.db.session_scope() as session:
            stmt = (
                select(DailyAttendance)
                .where(
                    DailyAttendance.user_id.in_(user_ids),
                    DailyAttendance.event_date == day,
                    DailyAttendance.is_deleted == False
                )
            )
            res = await session.execute(stmt)
            return res.scalars().all()

    async def get_by_person_and_date(
            self,
            person_id: UUID,
            day: date
    ) -> Optional[DailyAttendance]:
        """
        Xodim bir kunda ishga kelganmi — org_unit’dan qat’i nazar.
        """
        async with self.db.session_scope() as session:
            stmt = (
                select(DailyAttendance)
                .where(
                    DailyAttendance.user_id == person_id,
                    DailyAttendance.event_date == day,
                    DailyAttendance.is_deleted == False
                )
                .order_by(DailyAttendance.created_at.asc())
                .limit(1)
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def list_by_unit_and_month(self, unit_id: UUID, year: int, month: int) -> List[DailyAttendance]:
        async with self.db.session_scope() as session:
            first_day = date(year, month, 1)
            last_day = date(year, month, monthrange(year, month)[1])

            stmt = (
                select(DailyAttendance)
                .where(
                    DailyAttendance.org_unit_id == unit_id,
                    DailyAttendance.event_date >= first_day,
                    DailyAttendance.event_date <= last_day,
                    DailyAttendance.is_deleted == False
                )
                .order_by(
                    DailyAttendance.user_id,
                    DailyAttendance.event_date.asc()
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, instance: DailyAttendance) -> DailyAttendance:
        async with self.db.session_scope() as session:
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance

    async def upsert_daily(
            self,
            user_id: UUID,
            org_unit_id: UUID,
            date_: date,
            updates: Dict[str, any]
    ) -> DailyAttendance:
        existing = await self.get_by_person_and_date(user_id, date_)
        if existing:
            for k, v in updates.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            return await self.update(existing)

        new_instance = DailyAttendance(
            user_id=user_id,
            org_unit_id=org_unit_id,
            event_date=date_,
            **updates
        )
        return await self.create(new_instance)

    async def list_by_unit_and_date(self, unit_id: UUID, day: date) -> List[DailyAttendance]:
        async with self.db.session_scope() as session:
            stmt = (
                select(DailyAttendance)
                .where(
                    DailyAttendance.org_unit_id == unit_id,
                    DailyAttendance.event_date == day,
                    DailyAttendance.is_deleted == False
                )
                .order_by(DailyAttendance.first_entry.asc().nulls_last())
            )
            result = await session.execute(stmt)
            return result.scalars().all()


# ========================= MONTHLY ATTENDANCE ========================= #

class MonthlyAttendanceRepository(BaseRepository[MonthlyAttendanceSummary]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(MonthlyAttendanceSummary, db)

    async def create(self, instance: MonthlyAttendanceSummary) -> MonthlyAttendanceSummary:
        async with self.db.session_scope() as session:
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance

    async def get_by_user_and_month(self, user_id: UUID, year: int, month: int) -> Optional[MonthlyAttendanceSummary]:
        async with self.db.session_scope() as session:
            stmt = (
                select(MonthlyAttendanceSummary)
                .where(
                    MonthlyAttendanceSummary.user_id == user_id,
                    MonthlyAttendanceSummary.year == year,
                    MonthlyAttendanceSummary.month == month,
                    MonthlyAttendanceSummary.is_deleted == False
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def upsert_monthly(
            self,
            user_id: UUID,
            org_unit_id: UUID,
            year: int,
            month: int,
            updates: Dict[str, any]
    ) -> MonthlyAttendanceSummary:
        existing = await self.get_by_user_and_month(user_id, year, month)
        if existing:
            for k, v in updates.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            return await self.update(existing)

        new_instance = MonthlyAttendanceSummary(
            user_id=user_id,
            org_unit_id=org_unit_id,
            year=year,
            month=month,
            **updates
        )
        return await self.create(new_instance)

    async def list_by_unit_and_month(self, unit_id: UUID, year: int, month: int) -> List[MonthlyAttendanceSummary]:
        async with self.db.session_scope() as session:
            stmt = (
                select(MonthlyAttendanceSummary)
                .where(
                    MonthlyAttendanceSummary.org_unit_id == unit_id,
                    MonthlyAttendanceSummary.year == year,
                    MonthlyAttendanceSummary.month == month,
                    MonthlyAttendanceSummary.is_deleted == False
                )
                .order_by(MonthlyAttendanceSummary.total_worked_minutes.desc())
            )
            result = await session.execute(stmt)
            return result.scalars().all()


# ========================= DEVICE ========================= #

class DeviceRepository(BaseRepository[Device]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Device, db)

    async def create(self, instance: Device) -> Device:
        async with self.db.session_scope() as session:
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance

    async def mark_online(self, device_id: UUID):
        return await self.db.update_by_field(
            Device, "id", device_id, {"sync_status": "online"}
        )

    async def mark_offline(self, device_id: UUID):
        return await self.db.update_by_field(
            Device, "id", device_id, {"sync_status": "offline"}
        )

    async def get_by_ip(self, ip_address: str) -> Optional[Device]:
        async with self.db.session_scope() as session:
            stmt = (
                select(Device)
                .where(
                    Device.ip_address == ip_address,
                    Device.is_deleted == False
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_id(self, device_id: UUID) -> Optional[Device]:
        async with self.db.session_scope() as session:
            stmt = (
                select(Device)
                .where(
                    Device.id == device_id,
                    Device.is_deleted == False
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_active_devices(self) -> List[Device]:
        return await self.list({
            "is_active": True,
            "is_deleted": False
        })

    async def set_status(self, device_id: UUID, status: DeviceSyncStatus):
        return await self.db.update_by_field(
            Device,
            "id",
            device_id,
            {"sync_status": status}
        )

    async def update_sync_status(
            self,
            device_id: UUID,
            last_serial_no: int,
            last_event_time: datetime
    ):
        # 🔒 Ikkinchi himoya
        if last_event_time and last_event_time.tzinfo:
            last_event_time = last_event_time.replace(tzinfo=None)

        return await self.db.update_by_field(
            Device,
            "id",
            device_id,
            {
                "last_serial_no": last_serial_no,
                "last_event_time": last_event_time,
                "updated_at": datetime.utcnow()
            }
        )
