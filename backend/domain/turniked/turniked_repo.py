from __future__ import annotations
from typing import Optional, List, Dict
from uuid import UUID
from datetime import date, datetime,time

from sqlmodel import select, and_
from backend.domain.user.models import User

from backend.core.DatabaseService.base import DatabaseService
from backend.core.DatabaseService.repositories import BaseRepository
from backend.domain.turniked.models import AttendanceEvent, DailyAttendance, MonthlyAttendanceSummary, Device
from backend.domain.organization.org_repo import OrganizationRepository
from backend.domain.user.user_repo import UserRepository

WORK_START = time(9, 0, 0)
WORK_END = time(18, 0, 0)
LUNCH_START = time(13, 0, 0)
LUNCH_END = time(14, 0, 0)

class AttendanceEventRepository(BaseRepository[AttendanceEvent]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(AttendanceEvent, db)
        self.org_repo = OrganizationRepository(db)
        self.users = UserRepository(db)

    async def process_event(self, event: dict, device_id: UUID):
        print(event, 'event+++++++++++++++++++++++', event["employeeNoString"])
        """
        Real-time attendance handler — with row-level locking & invalid sequence filters.
        Safe for multi-event bursts.
        """
        if not event["employeeNoString"]:
            return

        async with self.db.session_scope() as session:

            # -------- USER MATCH --------
            user = await self.users.get_by_user_turniked_id(event["employeeNoString"])

            if not user:
                return  # unknown card

            print(user.id, '++++++++++++++++++++11111111111')

            # -------- TIME NORMALIZE --------
            now = event["time"]
            if isinstance(now, str):
                now = datetime.fromisoformat(now)  # Bu +05:00 bilan ishlaydi

            if now.tzinfo:
                now = now.replace(tzinfo=None)

            d = now.date()
            t = now.time()
            if event['minor'] == 75:
                direction = "IN"
            else:
                direction = "OUT"

            org_unit_id = await self.org_repo.get_org_unit_by_user_id_(user.id)
            print(org_unit_id, '123123321213321321321321321321321321')
            # -------- RAW EVENT LOG --------
            session.add(AttendanceEvent(
                user_id=user.id,
                device_id=device_id,
                direction=direction,
                turniked_id=event["employeeNoString"],
                event_date=d,
                event_time=t,
                timecontrol=f"{d}|{t}"
            ))

            # -------- DAILY FETCH (LOCKED) --------
            daily = (await session.execute(
                select(DailyAttendance)
                .where(
                    DailyAttendance.user_id == user.id,
                    DailyAttendance.event_date == d,
                    DailyAttendance.is_deleted == False
                )
                .with_for_update()  # ✅ row lock
            )).scalar_one_or_none()

            # -------- FIRST ENTRY --------
            if not daily and direction == "IN":
                daily = DailyAttendance(
                    user_id=user.id,
                    org_unit_id=org_unit_id,
                    device_id=device_id,
                    event_date=d,
                    first_entry=now,
                    last_exit=None,
                    entries_count=1,
                    alert_flag=True,
                    worked_minutes=0,
                    shift_start_time=WORK_START,
                    shift_end_time=WORK_END
                )
                session.add(daily)

                # -------- MONTH INIT (LOCKED) --------
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
                    m = MonthlyAttendanceSummary(
                        user_id=user.id,
                        org_unit_id=org_unit_id,
                        year=d.year,
                        month=d.month,
                        present_days=1,
                        total_days=1,
                        total_expected_minutes=480,
                        first_entry=now
                    )
                    session.add(m)

                return  # first IN done ✅

            # -------- NO DAILY BUT NOT IN → IGNORE INVALID --------
            if not daily:
                return

            # ❌ Prevent invalid OUT before IN
            if direction == "OUT" and not daily.first_entry:
                return

            # -------- FOLLOWING EVENTS --------
            daily.entries_count += 1

            # OUT → worked time calculation
            if direction == "OUT":
                last_entry = daily.last_exit or daily.first_entry
                if last_entry:
                    dt = now - last_entry
                    worked = max(0, int(dt.total_seconds() / 60))

                    # Exclude lunch hour
                    if LUNCH_START <= last_entry.time() <= LUNCH_END:
                        worked = 0

                    daily.worked_minutes += worked
                    daily.last_exit = now

                    # ---- UPDATE MONTHLY SAFELY ----
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

            # IN event → treat as re-entry log
            if direction == "IN":
                daily.last_exit = now

            session.add(daily)

    async def create(self, data: AttendanceEvent) -> AttendanceEvent:
        # Turnike event loglarini yaratish uchun ishlatiladi
        return await self.db.add(data)

    async def get_by_person_on_date(self, person_id: UUID, target_date: date) -> List[AttendanceEvent]:
        # Berilgan odam va sana bo'yicha barcha eventlarni olish
        return await self.list({
            "person_id": person_id,
            "event_date": target_date,
            "is_deleted": False
        })

    async def get_between_dates(self, person_id: UUID, start_date: date, end_date: date) -> List[AttendanceEvent]:
        # Odam uchun ma'lum sana oralig'idagi barcha eventlar
        async with self.db.session_scope() as session:
            stmt = select(AttendanceEvent).where(
                and_(
                    AttendanceEvent.person_id == person_id,
                    AttendanceEvent.event_date >= start_date,
                    AttendanceEvent.event_date <= end_date,
                    AttendanceEvent.is_deleted == False
                )
            ).order_by(AttendanceEvent.event_time.asc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_latest_by_device(self, device_id: UUID) -> Optional[AttendanceEvent]:
        # Qurilma uchun oxirgi yuborilgan eventni olish
        async with self.db.session_scope() as session:
            stmt = select(AttendanceEvent).where(
                AttendanceEvent.device_id == device_id,
                AttendanceEvent.is_deleted == False
            ).order_by(AttendanceEvent.event_time.desc()).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_event_hash(self, session, event_hash: str) -> Optional[AttendanceEvent]:
        async with self.db.session_scope() as session:
            stmt = select(AttendanceEvent).where(
                AttendanceEvent.hash_code == event_hash,
                AttendanceEvent.is_deleted == False
            ).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


class DailyAttendanceRepository(BaseRepository[DailyAttendance]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(DailyAttendance, db)

    async def get_by_person_and_date(self, person_id: UUID, day: date) -> Optional[DailyAttendance]:
        stmt = select(DailyAttendance).where(
            DailyAttendance.user_id == person_id,
            DailyAttendance.event_date == day,
            DailyAttendance.is_deleted == False
        )
        return await self.db.one_or_none(stmt)

    async def create(self, data: DailyAttendance) -> DailyAttendance:
        # Har kunlik hisobotni yaratish
        return await self.db.add(data)

    async def get_by_person_and_date(self, person_id: UUID, day: date) -> Optional[DailyAttendance]:
        # Kunlik hisobot olish (agar mavjud bo‘lsa)
        filters = {
            "person_id": person_id,
            "date": day,
            "is_deleted": False
        }
        return await self.db.one_or_none(select(DailyAttendance).where(and_(*[
            getattr(DailyAttendance, k) == v for k, v in filters.items()
        ])))

    async def upsert_daily(
        self,
        person_id: UUID,
        org_unit_id: UUID,
        date_: date,
        updates: Dict[str, any]
    ) -> DailyAttendance:
        # Kunlik ma'lumotni yangilash yoki yaratish
        existing = await self.get_by_person_and_date(person_id, date_)
        if existing:
            for k, v in updates.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            return await self.update(existing)
        else:
            new_instance = DailyAttendance(
                person_id=person_id,
                org_unit_id=org_unit_id,
                date=date_,
                **updates
            )
            return await self.create(new_instance)


class MonthlyAttendanceRepository(BaseRepository[MonthlyAttendanceSummary]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(MonthlyAttendanceSummary, db)

    async def create(self, data: MonthlyAttendanceSummary) -> MonthlyAttendanceSummary:
        # Oylik hisobotni yaratish
        return await self.db.add(data)

    async def get_by_person_and_month(self, person_id: UUID, year: int, month: int) -> Optional[MonthlyAttendanceSummary]:
        # Oylik statistikani olish
        return await self.db.one_or_none(select(MonthlyAttendanceSummary).where(
            MonthlyAttendanceSummary.person_id == person_id,
            MonthlyAttendanceSummary.year == year,
            MonthlyAttendanceSummary.month == month,
            MonthlyAttendanceSummary.is_deleted == False
        ))

    async def upsert_monthly(
        self,
        person_id: UUID,
        org_unit_id: UUID,
        year: int,
        month: int,
        updates: Dict[str, any]
    ) -> MonthlyAttendanceSummary:
        # Oylik statistikani yangilash yoki yaratish
        existing = await self.get_by_person_and_month(person_id, year, month)
        if existing:
            for k, v in updates.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            return await self.update(existing)
        else:
            new_instance = MonthlyAttendanceSummary(
                person_id=person_id,
                org_unit_id=org_unit_id,
                year=year,
                month=month,
                **updates
            )
            return await self.create(new_instance)


class DeviceRepository(BaseRepository[Device]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Device, db)

    async def create(self, data: Device) -> Device:
        # Yangi qurilma yaratish
        return await self.db.add(data)

    async def mark_online(self, device_id):
        return await self.db.update_by_field(
            model=Device,
            field_name="id",
            field_value=device_id,
            updates={"sync_status": "online"},
        )

    async def mark_offline(self, device_id):
        return await self.db.update_by_field(
            model=Device,
            field_name="id",
            field_value=device_id,
            updates={"sync_status": "offline"},
        )

    async def get_by_ip(self, ip_address: str) -> Optional[Device]:
        # Qurilmani IP manzili orqali olish (kelajakda ishlatish uchun foydali)
        return await self.db.one_or_none(select(Device).where(
            Device.ip_address == ip_address,
            Device.is_deleted == False
        ))

    async def get_active_devices(self) -> List[Device]:
        # Faol holatdagi barcha qurilmalar
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
        # Qurilmaning sinxron holatini yangilash (internet uzilgandan keyin sinxronlik uchun)
        return await self.db.update_by_field(
            model=Device,
            field_name="id",
            field_value=device_id,
            updates={
                "last_serial_no": last_serial_no,
                "last_event_time": last_event_time,
                "updated_at": datetime.utcnow()
            }
        )