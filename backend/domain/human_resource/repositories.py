from __future__ import annotations
from typing import List, Dict
from uuid import UUID
from sqlmodel import select, func, case
from uuid import UUID
from datetime import date
from sqlmodel import select
from backend.core.DatabaseService.base import DatabaseService
from backend.domain.turniked.models import DailyAttendance
from backend.domain.organization.models import OrgUnit, Position, Assignment
from backend.domain.user.models import User


class HRRepository:
    """
    HR uchun maxsus o‘qish (read-only) repository.
    OrgUnit ierarxiyasini tahlil qilish uchun ishlatiladi.
    """

    def __init__(self, db: DatabaseService):
        self.db = db

    async def get_active_users_by_org_unit(self, org_unit_id: UUID) -> int:
        """
        Berilgan org_unit ichida nechta faol xodim borligini qaytaradi.
        """
        today = date.today()
        async with self.db.session_scope() as session:
            stmt = (
                select(Assignment.user_id)
                .join(Position, Position.id == Assignment.position_id)
                .where(
                    Position.org_unit_id == org_unit_id,
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                    Assignment.valid_from <= today,
                    ((Assignment.valid_to.is_(None)) | (Assignment.valid_to >= today)),
                )
            )
            rows = (await session.execute(stmt)).scalars().all()
            return len(set(rows))

    async def get_children_units(self, parent_id: UUID) -> List[OrgUnit]:
        async with self.db.session_scope() as session:
            stmt = select(OrgUnit).where(
                OrgUnit.parent_id == parent_id,
                OrgUnit.is_deleted == False,
                OrgUnit.is_active == True,
            )
            return list((await session.execute(stmt)).scalars().all())

    async def get_root_units(self) -> List[OrgUnit]:
        async with self.db.session_scope() as session:
            stmt = select(OrgUnit).where(
                OrgUnit.parent_id.is_(None),
                OrgUnit.is_deleted == False,
                OrgUnit.is_active == True,
            )
            return list((await session.execute(stmt)).scalars().all())


    async def get_units_daily_summary(self, day: date):
        async with self.db.session_scope() as session:

            # 1️⃣ Barcha faol bo‘limlar
            units = (
                await session.execute(
                    select(OrgUnit)
                    .where(
                        OrgUnit.is_active == True,
                        OrgUnit.is_deleted == False
                    )
                )
            ).scalars().all()

            result = []

            for unit in units:
                # 2️⃣ Bo‘limdagi FAOL xodimlar (Assignment orqali)
                active_users_stmt = (
                    select(func.count(func.distinct(Assignment.user_id)))
                    .join(Position, Position.id == Assignment.position_id)
                    .where(
                        Position.org_unit_id == unit.id,
                        Assignment.status == "ACTIVE",
                        Assignment.is_deleted == False,
                        Assignment.valid_from <= day,
                        (Assignment.valid_to.is_(None) | (Assignment.valid_to >= day))
                    )
                )

                total_employees = (
                    await session.execute(active_users_stmt)
                ).scalar() or 0

                # 3️⃣ Shu kuni kelganlar (DailyAttendance BOR)
                present_stmt = (
                    select(func.count(func.distinct(DailyAttendance.user_id)))
                    .where(
                        DailyAttendance.org_unit_id == unit.id,
                        DailyAttendance.event_date == day,
                        DailyAttendance.first_entry.is_not(None),
                        DailyAttendance.is_deleted == False
                    )
                )

                present_count = (
                    await session.execute(present_stmt)
                ).scalar() or 0

                # 4️⃣ Kech kelganlar
                late_stmt = (
                    select(func.count(func.distinct(DailyAttendance.user_id)))
                    .where(
                        DailyAttendance.org_unit_id == unit.id,
                        DailyAttendance.event_date == day,
                        DailyAttendance.was_late == True,
                        DailyAttendance.is_deleted == False
                    )
                )

                late_count = (
                    await session.execute(late_stmt)
                ).scalar() or 0

                # 5️⃣ KELMAGANLAR — ENG MUHIM JOY
                absent_count = max(total_employees - present_count, 0)

                # 6️⃣ FOIZ
                attendance_rate = (
                    round((present_count / total_employees) * 100)
                    if total_employees > 0 else 0
                )

                result.append({
                    "unit_id": str(unit.id),
                    "name": unit.name,
                    "employeeCount": total_employees,
                    "presentCount": present_count,
                    "absentCount": absent_count,
                    "lateCount": late_count,
                    "attendanceRate": attendance_rate
                })

            return result