from __future__ import annotations
from typing import List, Dict
from backend.domain.user.models import User
from fastapi import HTTPException
from datetime import date
from backend.core.DatabaseService.base import DatabaseService
from backend.domain.human_resource.repositories import HRRepository
from backend.domain.organization.models import OrgUnit


class HRService:
    """
    HR panel uchun bo‘limlar ro‘yxatini shakllantiradi.
    """

    def __init__(self, db: DatabaseService):
        self.repo = HRRepository(db)

    async def get_hr_visible_units(self) -> List[Dict]:
        """
        HR panelda ko‘rinadigan bo‘limlar:
        - ichma-ich bo‘lsa ham
        - faqat real xodimlari bor ENG PAST bo‘limlar
        """
        result: List[Dict] = []

        roots = await self.repo.get_root_units()
        for root in roots:
            await self._walk_unit(root, result)

        return result

    async def get_units_daily_summary(self, current: User, day: date):
        # 🔒 SECURITY
        if not (current.is_superadmin or current.meta.get("role") == "HR_MANAGER"):
            raise HTTPException(status_code=403, detail="HR access only")

        return await self.repo.get_units_daily_summary(day)
    async def _walk_unit(self, unit: OrgUnit, out: List[Dict]):
        """
        Rekursiv yurish:
        - Agar bolalarida xodim bor bo‘lsa → pastga tush
        - Aks holda, agar o‘zida xodim bo‘lsa → HR listga qo‘sh
        """
        children = await self.repo.get_children_units(unit.id)

        has_child_with_staff = False
        for child in children:
            count = await self.repo.get_active_users_by_org_unit(child.id)
            if count > 0:
                has_child_with_staff = True
                await self._walk_unit(child, out)

        if not has_child_with_staff:
            own_staff = await self.repo.get_active_users_by_org_unit(unit.id)
            if own_staff > 0:
                out.append({
                    "id": unit.id,
                    "name": unit.name,
                    "unit_type": unit.unit_type,
                })
