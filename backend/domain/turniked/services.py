from __future__ import annotations
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from calendar import monthrange, day_name

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
from backend.domain.organization.services import AssignmentRepository
from backend.domain.user.services import UserRepository


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
        self.assign_repo = AssignmentRepository(self.db)
        self.user_repo = UserRepository(self.db)

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
            user_id=person_id,
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
            user_id=person_id,
            org_unit_id=org_unit_id,
            year=year,
            month=month,
            updates=updates,
        )

    async def get_monthly_by_person(self, person_id: UUID, year: int, month: int) -> Optional[MonthlyAttendanceSummary]:
        """Oylik ishtirokni olish."""
        return await self.monthly_repo.get_by_user_and_month(person_id, year, month)

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

    async def get_unit_daily_report(self, unit_id: UUID, day: date) -> List[Dict[str, Any]]:
        """
        Kunlik davomat + kirish / chiqish turniketlari
        """

        # 1️⃣ Bo‘limdagi aktiv xodimlar
        user_ids = await self.assign_repo.get_active_user_ids_by_unit(unit_id)
        if not user_ids:
            return []

        # 2️⃣ Kunlik attendance
        daily_rows = await self.daily_repo.list_by_users_and_date(user_ids, day)
        daily_by_user: Dict[UUID, DailyAttendance] = {r.user_id: r for r in daily_rows}

        # 3️⃣ Userlar
        users = await self.user_repo.get_many_by_ids(user_ids)
        user_map = {u.id: u.full_name or u.username for u in users}

        # 4️⃣ Lavozimlar
        titles = await self.assign_repo.get_active_titles_for_users(user_ids)
        title_map = {uid: ttl for uid, ttl in titles}

        out: List[Dict[str, Any]] = []

        # 5️⃣ 🔥 FETCH ALL DEVICES
        all_device_ids = set()
        for r in daily_rows:
            if r.first_device_id: all_device_ids.add(r.first_device_id)
            if r.last_device_id: all_device_ids.add(r.last_device_id)

        device_map: Dict[UUID, str] = {}
        if all_device_ids:
            devices = await self.device_repo.list_by_ids(list(all_device_ids))
            device_map = {d.id: d.name for d in devices}

        # 6️⃣ HAR BIR USER BO‘YICHA
        for uid in user_ids:
            d = daily_by_user.get(uid)

            first_device_name = device_map.get(d.first_device_id) if d and d.first_device_id else None
            last_device_name = device_map.get(d.last_device_id) if d and d.last_device_id else None

            out.append({
                "user_id": uid,
                "full_name": user_map.get(uid, "N/A"),
                "position": title_map.get(uid),
                "event_date": day.isoformat(),

                # === VAQTLAR ===
                "first_entry": d.first_entry.isoformat() if d and d.first_entry else None,
                "last_exit": d.last_exit.isoformat() if d and d.last_exit else None,

                # === TURNIKETLAR ===
                "first_device": first_device_name,
                "last_device": last_device_name,

                # === HISOBLAR ===
                "worked_minutes": d.worked_minutes if d else 0,
                "was_late": bool(d.was_late) if d else False,
                "left_early": bool(d.left_early) if d else False,
                "entries_count": d.entries_count if d else 0,
            })

        # 7️⃣ Rahbarni yuqoriga chiqarish
        out.sort(key=lambda x: (x["position"] or "").lower() != "bo‘lim boshlig‘i")

        return out

    # ==========================
    #  B) OYLIK — bo‘lim bo‘yicha
    # ==========================
    async def get_unit_monthly_report(self, unit_id: UUID, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Oylik jamlama: bo‘lim boshlig‘i + xodimlar.
        Daily mavjud bo‘lmasa ham (kelmagan bo‘lsa) user ro‘yxatida turadi; monthly yozuv bo‘lmasa — 0 bilan.
        """
        user_ids = await self.assign_repo.get_active_user_ids_by_unit(unit_id)
        if not user_ids:
            return []

        monthly_rows = await self.monthly_repo.list_by_unit_and_month(unit_id, year, month)
        monthly_by_user: Dict[UUID, MonthlyAttendanceSummary] = {r.user_id: r for r in monthly_rows}

        users = await self.user_repo.get_many_by_ids(user_ids)
        user_map = {u.id: u.full_name or u.username for u in users}

        titles = await self.assign_repo.get_active_titles_for_users(user_ids)
        title_map = {uid: ttl for uid, ttl in titles}

        out: List[Dict[str, Any]] = []
        for uid in user_ids:
            m = monthly_by_user.get(uid)
            out.append({
                "user_id": uid,
                "full_name": user_map.get(uid, "N/A"),
                "position": title_map.get(uid),
                "year": year,
                "month": month,
                "present_days": m.present_days if m else 0,
                "late_days": m.late_days if m else 0,
                "early_leave_days": m.early_leave_days if m else 0,
                "absent_days": m.absent_days if m else 0,
                "total_worked_minutes": m.total_worked_minutes if m else 0,
                "total_expected_minutes": m.total_expected_minutes if m else 0,
                "attendance_rate": m.attendance_rate if m else 0.0,
                "punctuality_score": m.punctuality_score if m else 0.0,
            })

        # Ixtiyoriy sort: boshliq oldinda
        out.sort(key=lambda x: (x["position"] or "").lower() != "bo‘lim boshlig‘i")
        return out

    async def get_unit_monthly_detailed_report(
            self,
            unit_id: UUID,
            year: int,
            month: int
    ) -> List[Dict[str, Any]]:
        """
        Oylik (kunma-kun) davomat hisobot:
        - Yakshanba kunlari SKIP qilinadi
        - Har bir xodim uchun: kunlar ro‘yxati + umumiy jamlar
        """

        # 1) Bo‘limdagi aktiv xodimlar (oy yakunida ham shular bo‘yicha hisobot)
        user_ids = await self.assign_repo.get_active_user_ids_by_unit(unit_id)
        if not user_ids:
            return []

        # 2) Shu bo‘lim + oy bo‘yicha mavjud DailyAttendance yozuvlarini oldindan olib qo‘yamiz
        monthly_daily_rows = await self.daily_repo.list_by_users_and_month(
            user_ids=user_ids,
            year=year,
            month=month
        )

        # (user_id, event_date) bo‘yicha index
        daily_index: Dict[tuple[UUID, date], DailyAttendance] = {
            (r.user_id, r.event_date): r for r in monthly_daily_rows
        }

        # 3) Userlar
        users = await self.user_repo.get_many_by_ids(user_ids)
        user_map = {u.id: (u.full_name or u.username) for u in users}

        # 4) Lavozimlar
        titles = await self.assign_repo.get_active_titles_for_users(user_ids)
        title_map = {uid: ttl for uid, ttl in titles}

        # 5) Shu oy uchun ish kunlari (yakshanbani SKIP)
        first_day = date(year, month, 1)
        last_day_num = monthrange(year, month)[1]

        working_days: List[date] = []
        for d in range(1, last_day_num + 1):
            current = date(year, month, d)
            # Python weekday(): Monday=0, Sunday=6
            if current.weekday() == 6:  # yakshanba → SKIP
                continue
            working_days.append(current)

        out: List[Dict[str, Any]] = []

        # 6) Har bir user bo‘yicha kunma-kun hisobot
        for uid in user_ids:
            days_rows: List[Dict[str, Any]] = []

            total_present_days = 0
            total_absent_days = 0
            total_worked_minutes = 0
            total_expected_minutes = 0

            for day_ in working_days:
                d_rec = daily_index.get((uid, day_))

                if d_rec:
                    is_absent = bool(d_rec.is_absent)
                    worked = d_rec.worked_minutes
                    was_late = bool(d_rec.was_late)
                    left_early = bool(d_rec.left_early)
                    first_entry = d_rec.first_entry
                    last_exit = d_rec.last_exit

                    # present/absent statistikasi
                    if worked > 0 or first_entry:
                        total_present_days += 1
                    else:
                        total_absent_days += 1

                    total_worked_minutes += worked
                    total_expected_minutes += (d_rec.expected_minutes or 0)
                else:
                    # Umuman DailyAttendance yo‘q → bu kun bo‘yicha absent deb qabul qilamiz
                    is_absent = True
                    worked = 0
                    was_late = False
                    left_early = False
                    first_entry = None
                    last_exit = None

                    total_absent_days += 1
                    total_expected_minutes += 480  # default ish kuni (8 soat)

                days_rows.append({
                    "date": day_,
                    "weekday": day_.weekday(),
                    "weekday_name": day_name[day_.weekday()],
                    "first_entry": first_entry,
                    "last_exit": last_exit,
                    "worked_minutes": worked,
                    "was_late": was_late,
                    "left_early": left_early,
                    "is_absent": is_absent,
                })

            out.append({
                "user_id": uid,
                "full_name": user_map.get(uid, "N/A"),
                "position": title_map.get(uid),
                "year": year,
                "month": month,
                "total_present_days": total_present_days,
                "total_absent_days": total_absent_days,
                "total_worked_minutes": total_worked_minutes,
                "total_expected_minutes": total_expected_minutes,
                "days": days_rows,
            })

        # 7) Rahbarni yuqoriga chiqarish (kunlik hisobotdagidek)
        out.sort(key=lambda x: (x["position"] or "").lower() != "bo‘lim boshlig‘i")
        return out
