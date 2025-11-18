from __future__ import annotations
from datetime import date, datetime,time
from typing import Optional, List, Dict
from calendar import monthrange
from sqlmodel import select
from uuid import UUID

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

class AttendanceEventRepository(BaseRepository[AttendanceEvent]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(AttendanceEvent, db)
        self.org_repo = OrganizationRepository(db)
        self.users = UserRepository(db)
        self.device_repo = DeviceRepository(db)

    async def process_event(self, event: dict, device_id: UUID):
        # logger.debug(f"Incoming turniket event: {event}")

        if not event.get("employeeNoString"):
            return

        async with self.db.session_scope() as session:
            user = await self.users.get_by_user_turniked_id(event["employeeNoString"])
            if not user:
                # logger.warning(f"Unknown turniket ID: {event['employeeNoString']}")
                return
            device = await self.device_repo.get_by_id(device_id)
            if not device:
                logger.warning(f"Unknown device ID: {device_id}")
                return

            now = event["time"]
            if isinstance(now, str):
                now = datetime.fromisoformat(now)

            if now.tzinfo:
                now = now.replace(tzinfo=None)

            d = now.date()
            t = now.time()
            direction = device.source_system

            org_unit_id = await self.org_repo.get_org_unit_by_user_id_(user.id)

            # Save raw event
            session.add(AttendanceEvent(
                user_id=user.id,
                device_id=device_id,
                direction=direction,
                turniked_id=event["employeeNoString"],
                event_date=d,
                event_time=t,
                timecontrol=f"{d}|{t}"
            ))

            # DAILY RECORD
            daily = (await session.execute(
                select(DailyAttendance)
                .where(
                    DailyAttendance.user_id == user.id,
                    DailyAttendance.event_date == d,
                    DailyAttendance.is_deleted == False
                )
                .with_for_update()
            )).scalar_one_or_none()

            # First IN of the day
            if not daily and direction == "IN":
                daily = DailyAttendance(
                    user_id=user.id,
                    org_unit_id=org_unit_id,
                    device_id=device_id,
                    event_date=d,
                    first_entry=now,
                    first_device_id=device_id,
                    last_exit=None,
                    entries_count=1,
                    alert_flag=True,
                    worked_minutes=0,
                    shift_start_time=WORK_START,
                    shift_end_time=WORK_END
                )
                session.add(daily)

                # MONTH init
                m = (await session.execute(
                    select(MonthlyAttendanceSummary)
                    .where(
                        MonthlyAttendanceSummary.user_id == user.id,
                        MonthlyAttendanceSummary.year == d.year,
                        MonthlyAttendanceSummary.month == d.month,
                        MonthlyAttendanceSummary.is_deleted == False
                    )
                    .with_for_update()
                )).scalar_one_or_none()

                if not m:
                    session.add(MonthlyAttendanceSummary(
                        user_id=user.id,
                        org_unit_id=org_unit_id,
                        year=d.year,
                        month=d.month,
                        present_days=1,
                        total_days=1,
                        total_expected_minutes=480,
                        first_entry=now
                    ))

                return

            if not daily:
                return

            # Invalid OUT before IN
            if direction == "OUT" and not daily.first_entry:
                return

            daily.entries_count += 1

            # OUT → calc
            if direction == "OUT":
                last_entry = daily.last_exit or daily.first_entry
                if last_entry:
                    dt = now - last_entry
                    worked = max(0, int(dt.total_seconds() / 60))

                    if LUNCH_START <= last_entry.time() <= LUNCH_END:
                        worked = 0

                    daily.worked_minutes += worked
                    daily.last_exit = now

                    m = (await session.execute(
                        select(MonthlyAttendanceSummary)
                        .where(
                            MonthlyAttendanceSummary.user_id == user.id,
                            MonthlyAttendanceSummary.year == d.year,
                            MonthlyAttendanceSummary.month == d.month,
                            MonthlyAttendanceSummary.is_deleted == False
                        )
                        .with_for_update()
                    )).scalar_one_or_none()

                    if m:
                        m.total_worked_minutes += worked
                        m.last_exit = now

            if direction == "IN":
                # Faqat entry count oshadi
                pass

            if direction == "OUT":
                daily.last_exit = now

            session.add(daily)

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

    async def get_by_person_and_date(self, person_id: UUID, day: date) -> Optional[DailyAttendance]:
        async with self.db.session_scope() as session:
            stmt = (
                select(DailyAttendance)
                .where(
                    DailyAttendance.user_id == person_id,
                    DailyAttendance.event_date == day,
                    DailyAttendance.is_deleted == False
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

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

    async def update_sync_status(
        self,
        device_id: UUID,
        last_serial_no: int,
        last_event_time: datetime
    ) -> Optional[UUID]:
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