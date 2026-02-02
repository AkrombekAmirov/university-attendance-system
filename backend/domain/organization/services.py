from __future__ import annotations

from typing import List, Optional, Dict
from fastapi import HTTPException
from datetime import date
from uuid import UUID

from backend.domain.organization.org_repo import (
    OrganizationRepository, OrgUnitRepository, PositionRepository, ReportingLinkRepository,
    AssignmentRepository, PositionClosureRepository
)
from backend.core.DatabaseService.base import DatabaseService
from backend.domain.organization.models import Organization, OrgUnit, Position, ReportingLink, Assignment, \
    PositionClosure
from backend.domain.turniked.turniked_repo import DeviceRepository
from backend.domain.turniked.models import Device


class OrganizationService:
    """Business layer — faqat biznes qoidalarni boshqaradi, scope'lar faqat repo ichida."""

    def __init__(self, db: Optional[DatabaseService] = None):
        self.db = db or DatabaseService()
        self.org_repo = OrganizationRepository(self.db)
        self.unit_repo = OrgUnitRepository(self.db)
        self.pos_repo = PositionRepository(self.db)
        self.link_repo = ReportingLinkRepository(self.db)
        self.assign_repo = AssignmentRepository(self.db)
        self.closure_repo = PositionClosureRepository(self.db)
        self.device_repo = DeviceRepository(self.db)

    # ---------------- ORGANIZATION ----------------
    async def create_organization(self, name: str, code: Optional[str] = None,
                                  description: Optional[str] = None) -> Organization:
        return await self.org_repo.create_organization(name, code, description)

    async def get_all_organizations(self) -> List[Organization]:
        return await self.org_repo.get_all()

    async def get_by_code(self, code: str) -> Optional[Organization]:
        return await self.org_repo.get_by_code(code)

    async def search_organizations(self, keyword: str) -> List[Organization]:
        return await self.org_repo.search(keyword)

    async def get_org_unit_by_user_id(self, user_id: UUID) -> Optional[UUID]:
        return await self.unit_repo.get_org_unit_by_user_id(user_id)

    # ---------------- ORG UNIT ----------------
    async def get_user_scope(self, user_id: UUID):
        # 1) User position topish
        pos_id = await self.unit_repo.get_active_position_by_user(user_id)
        if not pos_id:
            return {"units": [], "positions": [], "users": [user_id]}

        # 2) Shu pozitsiyaga bo‘ysunuvchilar
        positions = await self.closure_repo.get_child_positions(pos_id)

        # 3) Ularga biriktirilgan users
        users = await self.assign_repo.get_users_by_positions(positions)

        return {
            "positions": positions,
            "users": users if users else [user_id]
        }

    async def create_org_unit(self, organization_id: UUID, name: str, unit_type: str,
                              parent_id: Optional[UUID] = None, order_no: int = 0) -> OrgUnit:
        return await self.unit_repo.create_unit(organization_id, name, unit_type, parent_id, order_no)

    async def get_org_tree(self, organization_id: UUID) -> Dict:
        return await self.unit_repo.get_tree(organization_id)

    # ---------------- POSITION ----------------
    async def create_position(self,
                              org_unit_id: UUID,
                              title: str,
                              is_unique: bool = True,
                              quota: Optional[int] = None) -> Position:
        return await self.pos_repo.create_position(org_unit_id, title, is_unique, quota)

    async def get_positions_by_unit(self, org_unit_id: UUID) -> List[Position]:
        return await self.pos_repo.get_by_unit(org_unit_id)

    async def get_position_list(self) -> List[Position]:
        return await self.pos_repo.get_position_list()

    async def get_positions_by_org_unit(self, position_id: UUID) -> List[Position]:
        return await self.pos_repo.get_by_unit(position_id)

    # ---------------- REPORTING LINK ----------------
    async def create_reporting_link(self, parent_position_id: UUID,
                                    child_position_id: UUID,
                                    relation_type: str = "LINE") -> ReportingLink:
        return await self.link_repo.create_reporting_link(parent_position_id, child_position_id, relation_type)

    async def check_reporting_link_exists(self, parent_position_id: UUID, child_position_id: UUID) -> bool:
        link = await self.link_repo.check_if_exists(parent_position_id, child_position_id)
        return link is not None

    async def get_reporting_links_by_parent(self, parent_position_id: UUID) -> List[ReportingLink]:
        return await self.link_repo.get_by_parent(parent_position_id)

    async def get_reporting_links_by_child(self, child_position_id: UUID) -> List[ReportingLink]:
        return await self.link_repo.get_by_child(child_position_id)

    async def get_direct_manager(self, child_position_id: UUID) -> Optional[ReportingLink]:
        return await self.link_repo.get_direct_manager(child_position_id)

    # ---------------- ASSIGNMENT ----------------
    async def get_by_user_assignment(self, user_id: UUID) -> List[Assignment]:
        return await self.assign_repo.get_by_user(user_id)

    async def get_by_position_assignment(self, position_id: UUID) -> List[Assignment]:
        return await self.assign_repo.get_by_position(position_id)

    async def create_assignment(self,
                                user_id: UUID,
                                position_id: UUID,
                                valid_from: date,
                                valid_to: Optional[date] = None,
                                status: str = "ACTIVE") -> Assignment:
        return await self.assign_repo.create_assignment(
            user_id=user_id,
            position_id=position_id,
            valid_from=valid_from or date.today(),
            valid_to=valid_to,
            status=status,
        )

    async def list_assignments(self) -> List[Assignment]:
        return await self.assign_repo.list_assignments()
    # --------------------------------------------
    # Userni lavozimga XAVFSIZ biriktirish
    # --------------------------------------------
    async def assign_user_to_position(
        self,
        *,
        user_id: UUID,
        position_id: UUID,
        effective_date: date | None = None,
    ) -> Assignment:

        effective_date = effective_date or date.today()

        async with self.db.session_scope() as session:

            position = await self.pos_repo.get_by_id(position_id)
            if not position or position.is_deleted:
                raise HTTPException(404, "Lavozim topilmadi")

            # 1️⃣ Agar position unique bo‘lsa → eski userni chiqaramiz
            if position.is_unique:
                await self.assign_repo.terminate_active_by_position(
                    position_id,
                    terminated_at=effective_date,
                )

            # 2️⃣ Agar user boshqa joyda ACTIVE bo‘lsa → bo‘shatamiz
            await self.assign_repo.terminate_active_by_user(
                user_id,
                terminated_at=effective_date,
            )

            # 3️⃣ Yangi assignment
            assignment = Assignment(
                user_id=user_id,
                position_id=position_id,
                status="ACTIVE",
                valid_from=effective_date,
            )

            session.add(assignment)
            await session.flush()
            await session.refresh(assignment)

            return assignment

    # --------------------------------------------
    # Userni BUTUNLAY bo‘shatish
    # --------------------------------------------
    async def unassign_user(
        self,
        *,
        user_id: UUID,
        effective_date: date | None = None,
    ) -> int:

        effective_date = effective_date or date.today()

        return await self.assign_repo.terminate_active_by_user(
            user_id,
            terminated_at=effective_date,
        )

    # --------------------------------------------
    # Lavozimdagi userni ALMASHTIRISH
    # --------------------------------------------
    async def replace_position_user(
        self,
        *,
        position_id: UUID,
        new_user_id: UUID,
        effective_date: date | None = None,
    ) -> Assignment:

        effective_date = effective_date or date.today()

        async with self.db.session_scope() as session:

            position = await self.pos_repo.get_by_id(position_id)
            if not position:
                raise HTTPException(404, "Lavozim topilmadi")

            # 1️⃣ Eski userni chiqaramiz
            await self.assign_repo.terminate_active_by_position(
                position_id,
                terminated_at=effective_date,
            )

            # 2️⃣ Yangi user boshqa joyda bo‘lsa → bo‘shatamiz
            await self.assign_repo.terminate_active_by_user(
                new_user_id,
                terminated_at=effective_date,
            )

            # 3️⃣ Yangi assignment
            assignment = Assignment(
                user_id=new_user_id,
                position_id=position_id,
                status="ACTIVE",
                valid_from=effective_date,
            )

            session.add(assignment)
            await session.flush()
            await session.refresh(assignment)

            return assignment

    # ---------------- POSITION CLOSURE ----------------
    async def create_position_closure(self,
                                      parent_position_id: UUID,
                                      child_position_id: UUID,
                                      depth: int = 1) -> PositionClosure:
        return await self.closure_repo.create_closure(parent_position_id, child_position_id, depth)

    async def insert_closure(self,
                             child_id: UUID,
                             parent_id: UUID,
                             created_by: Optional[UUID] = None) -> list[PositionClosure]:
        return await self.closure_repo.insert_closure(child_id, parent_id)

    async def bulk_create_position_closures(self, closures: List[PositionClosure]) -> List[PositionClosure]:
        return await self.closure_repo.bulk_create_closures(closures)

    async def get_position_closures_by_parent(self, parent_position_id: UUID) -> List[PositionClosure]:
        return await self.closure_repo.get_by_parent(parent_position_id)

    async def get_position_closures_by_child(self, child_position_id: UUID) -> List[PositionClosure]:
        return await self.closure_repo.get_by_child(child_position_id)

    async def get_direct_parent_closure(self, child_position_id: UUID) -> Optional[PositionClosure]:
        return await self.closure_repo.get_direct_chain(child_position_id)

    async def check_closure_exists(self, parent_position_id: UUID, child_position_id: UUID) -> bool:
        closure = await self.closure_repo.check_if_exists(parent_position_id, child_position_id)
        return closure is not None

    async def delete_closures_by_position(self, position_id: UUID) -> int:
        return await self.closure_repo.delete_closure_by_position(position_id)
