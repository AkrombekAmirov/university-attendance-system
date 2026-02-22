from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status

from backend.core.DatabaseService.base import DatabaseService
from backend.domain.human_resource.services import HRService
from backend.domain.turniked.services import TurnikedService
from backend.domain.user.models import User


@dataclass
class HRController:
    """
    HR (Kadrlar bo‘limi) uchun controller.
    Faqat o‘qish / tahlil qilish (read-only).
    """
    db: DatabaseService

    def __post_init__(self):
        self.hr_svc = HRService(self.db)
        self.turniked_svc = TurnikedService(self.db)
    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def _ensure_hr_access(self, current: User):
        """
        HR huquqini tekshirish.
        Hozircha soddaroq:
        - superadmin → OK
        - meta orqali hr flag → OK
        """
        if current.is_superadmin:
            return

        # meta ichida {"is_hr": true} bo‘lsa yetarli
        print(current.meta.get("role"))
        if current.meta and current.meta.get("role") == "HR_MANAGER":
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR access required"
        )

    # -------------------------------------------------
    # Public endpoints logic
    # -------------------------------------------------
    async def get_hr_units(self, current: User) -> List[Dict]:
        """
        HR chap panel uchun bo‘limlar ro‘yxati.
        Ichma-ich bo‘lsa ham, faqat real xodimi bor
        ENG PAST bo‘limlar qaytariladi.
        """
        self._ensure_hr_access(current)

        return await self.hr_svc.get_hr_visible_units()

    async def hr_unit_daily_attendance(
            self,
            *,
            current: User,
            unit_id: UUID,
            day: date
    ):
        self._ensure_hr_access(current)


        # ✅ MUHIM: mavjud logikani to‘liq reuse qilamiz
        return await self.turniked_svc.get_unit_daily_report(
            unit_id=unit_id,
            day=day
        )

    async def units_daily_summary(self, current: User, day: date):
        return await self.hr_svc.get_units_daily_summary(current, day)
