from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from datetime import date
from typing import List, Optional, Any, Coroutine
from fastapi import Request, HTTPException, Query
from backend.core.DatabaseService import DatabaseService
from backend.core.LoggingService import logger
from backend.core.audit import audit_action
from backend.core.security import get_current_user
from backend.domain.user.models import User
from backend.domain.organization.services import OrganizationService
from backend.interfaces.turniked.schemas import (
    TurniketLoginIn, TurniketTokenResponse, MeTurniketOut,
    StaffOut, OrgTreeOut, DailyRowOut, MonthlyRowOut
)
from backend.domain.user.services import UserService, UserStaffDTO
from backend.domain.turniked.services import TurnikedService


@dataclass
class TurniketController:
    db: DatabaseService
    request: Request

    def __post_init__(self):
        self.user_svc = UserService(self.db)
        self.org_svc = OrganizationService(self.db)
        self.turniked_svc = TurnikedService(self.db)

    def _fp(self):
        return self.request.headers.get("x-fp")

    def _ua(self):
        return self.request.headers.get("user-agent")

    def _ip(self) -> str:
        return self.request.client.host if self.request.client else "unknown"

    # -------------------------
    # AUTH LOGIN
    # -------------------------
    @audit_action(action="AUTH.STAFF.LOGIN", entity_type="User")
    async def login(self, payload: TurniketLoginIn) -> TurniketTokenResponse:
        user = await self.user_svc.authenticate(payload.username, payload.password, ip=self._ip())
        if not user:
            raise HTTPException(status_code=401, detail="Login yoki parol noto‘g‘ri")

        if user.is_superadmin:
            raise HTTPException(status_code=403, detail="Superadmin uchun emas")

        access, refresh = await self.user_svc.issue_tokens(
            user, fingerprint=self._fp(), user_agent=self._ua(), ip=self._ip()
        )

        logger.info("✅ Staff login successful: {}", user.username)

        return TurniketTokenResponse(
            access_token=access,
            refresh_token=refresh,
            redirect_path="/staff/users",
            expires_in=60 * 60 * 24
        )

    # -------------------------
    # ME
    # -------------------------
    async def me(self, current: User) -> MeTurniketOut:
        a = await self.org_svc.get_by_user_assignment(current.id)
        pos = await self.org_svc.pos_repo.get_by_id(a[0].position_id) if a else None

        return MeTurniketOut(
            id=current.id,
            username=current.username,
            full_name=current.full_name,
            position=pos.title if pos else None,
            org_unit_id=pos.org_unit_id if pos else None
        )

    # -------------------------
    # MY SUBORDINATES (FLAT)
    # -------------------------
    async def my_staff(self, current: User, unit_id: UUID | None) -> list[UserStaffDTO]:
        return await self.user_svc.get_staff_by_unit(current.id, unit_id)

    # -------------------------
    # ORG TREE
    # -------------------------
    async def org_tree(self, current: User):
        subordinate_ids = await self._get_subordinate_user_ids(current.id)
        return await self.user_svc.build_org_tree(current.id, subordinate_ids)

    # -------------------------
    # INTERNAL hierarchy helper
    # -------------------------
    async def _get_subordinate_user_ids(self, user_id: UUID) -> List[UUID]:
        """
           Foydalanuvchining barcha pastki lavozimlaridagi (cheksiz chuqurlikdagi) xodimlar ro‘yxatini qaytaradi.
           """

        # 1. Foydalanuvchining ACTIVE lavozimini topamiz
        assignments = await self.org_svc.get_by_user_assignment(user_id)
        if not assignments:
            return []

        root_position_id = assignments[0].position_id

        # 2. root_position_id ostidagi barcha lavozimlarni closure jadvalidan olamiz
        closures = await self.org_svc.get_position_closures_by_parent(root_position_id)
        all_child_ids = [c.child_position_id for c in closures if c.depth > 0]

        # 3. Barcha pastki lavozimlardagi foydalanuvchilarning ID sini yig'amiz
        user_ids: set[UUID] = set()

        for child_position_id in all_child_ids:
            assigns = await self.org_svc.get_by_position_assignment(child_position_id)
            for a in assigns:
                user_ids.add(a.user_id)

        return list(user_ids)

    async def unit_daily_attendance(self, current: User, unit_id: UUID = Query(...),
                                    day: date = Query(default_factory=date.today)):
        return await self.turniked_svc.get_unit_daily_report(unit_id, day)

    async def unit_monthly_attendance(self, current: User, unit_id: UUID = Query(...),
                                      year: int = Query(..., ge=2000, le=2100),
                                      month: int = Query(..., ge=1, le=12)):
        return await self.turniked_svc.get_unit_monthly_report(unit_id, year, month)

    async def unit_monthly_attendance_detailed(self, current: User, unit_id: UUID = Query(...), year: int = Query(...), month: int = Query(...)):
        return await self.turniked_svc.get_unit_monthly_detailed_report(unit_id=unit_id, year=year, month=month)
