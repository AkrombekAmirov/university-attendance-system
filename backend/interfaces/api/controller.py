from __future__ import annotations
from dataclasses import dataclass
from fastapi import Request, HTTPException
from typing import Optional, List, Dict
from uuid import UUID
from datetime import date

from backend.core.DatabaseService.base import DatabaseService
from backend.core.LoggingService import logger
from backend.core.audit import audit_action
from backend.core.config import get_settings
from backend.domain.organization.services import OrganizationService
from backend.domain.user.services import UserService
from backend.domain.user.models import User
from backend.interfaces.api.schemas import (
    OrganizationCreateIn, OrganizationOut,
    OrgUnitCreateIn, OrgUnitOut,
    PositionCreateIn, PositionOut,
    AssignmentCreateIn, AssignmentOut,
    ReportingLinkCreateIn, ReportingLinkOut,
    PositionClosureCreateIn, PositionClosureOut,
)


@dataclass
class OrganizationController:
    db: DatabaseService
    request: Request

    def __post_init__(self):
        self.settings = get_settings()
        self.svc = OrganizationService(self.db)
        self.user_svc = UserService(self.db)

    # ======================================================
    # ORGANIZATION
    # ======================================================

    @audit_action(action="ORG.CREATE", entity_type="Organization")
    async def create_organization(self, payload: OrganizationCreateIn, actor: User) -> OrganizationOut:
        if not actor.is_superadmin:
            raise HTTPException(status_code=403, detail="Only superadmin can create organizations")

        try:
            existing = await self.svc.get_by_code(payload.code)
            if existing:
                raise HTTPException(status_code=400, detail="Organization with this code already exists")

            org = await self.svc.create_organization(
                name=payload.name,
                code=payload.code,
                description=payload.description,
            )
            logger.info("🏢 Organization created: {} ({})", org.name, org.code)
            return OrganizationOut.from_orm(org)
        except Exception as e:
            logger.exception("❌ Organization creation failed: {}", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def list_organizations(self) -> List[OrganizationOut]:
        orgs = await self.svc.get_all_organizations()
        return orgs

    async def search_organizations(self, keyword: str) -> List[OrganizationOut]:
        orgs = await self.svc.search_organizations(keyword)
        return [OrganizationOut.from_orm(o) for o in orgs]

    # ======================================================
    # ORG UNIT
    # ======================================================

    @audit_action(action="UNIT.CREATE", entity_type="OrgUnit")
    async def create_org_unit(self, payload: OrgUnitCreateIn, actor: User) -> OrgUnitOut:
        if not actor.is_superadmin:
            raise HTTPException(status_code=403, detail="Only superadmin can create organization units")

        unit = await self.svc.create_org_unit(
            organization_id=payload.organization_id,
            name=payload.name,
            unit_type=payload.unit_type,
            parent_id=payload.parent_id,
        )
        logger.info("🏛️ Org unit created: {}", unit.name)
        return OrgUnitOut.from_orm(unit)

    async def get_org_tree(self, organization_id: UUID) -> Dict:
        return await self.svc.get_org_tree(organization_id)

    @audit_action(action="POSITION.CREATE", entity_type="Position")
    async def create_position(self, payload: PositionCreateIn, actor: User) -> PositionOut:
        if not actor.is_superadmin:
            raise HTTPException(status_code=403, detail="Faqat superadmin lavozim yarata oladi")

        try:
            unit = await self.svc.unit_repo.get(payload.org_unit_id)
            if not unit:
                raise HTTPException(status_code=404, detail="Bo‘linma topilmadi")

            if payload.is_unique:
                existing = await self.svc.pos_repo.get_existing(payload.org_unit_id, payload.title)
                if existing:
                    raise HTTPException(status_code=400, detail="Bu lavozim allaqachon mavjud")

            position = await self.svc.create_position(
                org_unit_id=payload.org_unit_id,
                title=payload.title,
                is_unique=payload.is_unique,
                quota=payload.quota,
            )

            if payload.parent_position_id:
                exists = await self.svc.check_reporting_link_exists(
                    parent_position_id=payload.parent_position_id,
                    child_position_id=position.id
                )

                if not exists:
                    await self.svc.create_reporting_link(
                        parent_position_id=payload.parent_position_id,
                        child_position_id=position.id,
                        relation_type="LINE"
                    )

                await self.svc.insert_closure(
                    child_id=position.id,
                    parent_id=payload.parent_position_id,
                    created_by=actor.id
                )

            logger.info("✅ Position created successfully: {} ({})", position.title, position.id)
            return PositionOut.model_validate(position)

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("❌ Position yaratishda xatolik: {}", str(e))
            raise HTTPException(status_code=500, detail="Ichki tizim xatoligi")

    @audit_action(action="POSITION.BY_UNIT", entity_type="Position")
    async def get_positions_by_unit_id(self, org_unit_id: UUID, actor: User) -> List[PositionOut]:
        """Berilgan bo‘limga tegishli lavozimlar ro‘yxatini qaytaradi."""
        try:
            if not actor.is_superadmin:
                raise HTTPException(status_code=403, detail="You are not authorized to view positions by unit")

            positions = await self.svc.get_positions_by_org_unit(org_unit_id)
            return [PositionOut.from_orm(pos) for pos in positions]
        except Exception as e:
            logger.exception("❌ Error fetching positions by unit: {}", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @audit_action(action="ASSIGNMENT.CREATE", entity_type="Assignment")
    async def create_assignment(self, payload: AssignmentCreateIn, actor: User) -> AssignmentOut:
        if not actor.is_superadmin:
            raise HTTPException(status_code=403, detail="Faqat superadmin biriktirishni amalga oshirishi mumkin")

        try:
            position = await self.user_svc.get_user_position(payload.position_id)
            if not position:
                raise HTTPException(status_code=404, detail="Lavozim topilmadi")

            assignment = await self.svc.create_assignment(
                user_id=payload.user_id,
                position_id=payload.position_id,
                valid_from=payload.valid_from or date.today(),
                valid_to=payload.valid_to,
                status=payload.status or "ACTIVE",
            )

            return AssignmentOut.from_orm(assignment)

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("❌ Assignment yaratishda xatolik: {}", str(e))
            raise HTTPException(500, detail="Ichki tizim xatoligi")

    async def list_assignments(self):
        return await self.svc.list_assignments()

    async def get_position_list(self, current_user: User):
        positions = await self.svc.get_position_list()
        return [PositionOut.from_orm(p) for p in positions]

    # ================================
    # REPORTING LINK
    # ================================

    @audit_action(action="REPORTING_LINK.CREATE", entity_type="ReportingLink")
    async def create_reporting_link(self, payload: ReportingLinkCreateIn, actor: User) -> ReportingLinkOut:
        if not actor.is_superadmin:
            raise HTTPException(status_code=403, detail="Only superadmin can create reporting links")

        try:
            existing = await self.svc.link_repo.check_if_exists(
                parent_position_id=payload.parent_position_id,
                child_position_id=payload.child_position_id
            )
            if existing:
                raise HTTPException(status_code=400, detail="This reporting relationship already exists")

            link = await self.svc.create_reporting_link(
                parent_position_id=payload.parent_position_id,
                child_position_id=payload.child_position_id,
                relation_type=payload.relation_type
            )

            logger.info("🔗 ReportingLink created: {} ➝ {}", payload.parent_position_id, payload.child_position_id)
            return ReportingLinkOut.from_orm(link)

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("❌ Failed to create ReportingLink: {}", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @audit_action(action="REPORTING_LINK.GET_BY_PARENT", entity_type="ReportingLink")
    async def get_reporting_links_by_parent(self, parent_position_id: UUID, actor: User) -> List[ReportingLinkOut]:
        try:
            links = await self.svc.get_reporting_links_by_parent(parent_position_id)
            return [ReportingLinkOut.from_orm(link) for link in links]
        except Exception as e:
            logger.exception("❌ Error getting reporting links by parent: {}", str(e))
            raise HTTPException(status_code=500, detail="Failed to fetch reporting links")

    @audit_action(action="REPORTING_LINK.GET_BY_CHILD", entity_type="ReportingLink")
    async def get_reporting_links_by_child(self, child_position_id: UUID, actor: User) -> List[ReportingLinkOut]:
        try:
            links = await self.svc.get_reporting_links_by_child(child_position_id)
            return [ReportingLinkOut.from_orm(link) for link in links]
        except Exception as e:
            logger.exception("❌ Error getting reporting links by child: {}", str(e))
            raise HTTPException(status_code=500, detail="Failed to fetch reporting links")

    @audit_action(action="REPORTING_LINK.GET_DIRECT_MANAGER", entity_type="ReportingLink")
    async def get_direct_manager(self, child_position_id: UUID, actor: User) -> Optional[ReportingLinkOut]:
        try:
            link = await self.svc.get_direct_manager(child_position_id)
            if not link:
                raise HTTPException(status_code=404, detail="Direct manager not found")
            return ReportingLinkOut.from_orm(link)
        except Exception as e:
            logger.exception("❌ Error getting direct manager: {}", str(e))
            raise HTTPException(status_code=500, detail="Failed to get direct manager")

    # ======================================================
    # POSITION CLOSURE
    # ======================================================

    @audit_action(action="CLOSURE.CREATE", entity_type="PositionClosure")
    async def create_position_closure(self, parent_position_id: UUID, child_position_id: UUID, actor: User) -> PositionClosureOut:
        try:
            exists = await self.svc.check_closure_exists(parent_position_id, child_position_id)
            if exists:
                raise HTTPException(status_code=400, detail="This reporting hierarchy already exists")

            closure = await self.svc.create_position_closure(
                parent_position_id=parent_position_id,
                child_position_id=child_position_id,
                depth=1
            )
            logger.info("🔗 Position closure created: {} → {}", parent_position_id, child_position_id)
            return PositionClosureOut.from_orm(closure)
        except Exception as e:
            logger.exception("❌ Failed to create position closure: {}", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def bulk_create_position_closures(self, closures: List[PositionClosureCreateIn], actor: User) -> List[PositionClosureOut]:
        try:
            created = await self.svc.bulk_create_position_closures(closures)
            return [PositionClosureOut.from_orm(c) for c in created]
        except Exception as e:
            logger.exception("❌ Bulk closure creation failed: {}", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_closures_by_parent(self, parent_position_id: UUID) -> List[PositionClosureOut]:
        closures = await self.svc.get_position_closures_by_parent(parent_position_id)
        return [PositionClosureOut.from_orm(c) for c in closures]

    async def get_closures_by_child(self, child_position_id: UUID) -> List[PositionClosureOut]:
        closures = await self.svc.get_position_closures_by_child(child_position_id)
        return [PositionClosureOut.from_orm(c) for c in closures]

    async def get_direct_manager_closure(self, child_position_id: UUID) -> Optional[PositionClosureOut]:
        closure = await self.svc.get_direct_parent_closure(child_position_id)
        return PositionClosureOut.from_orm(closure) if closure else None

    async def check_if_closure_exists(self, parent_position_id: UUID, child_position_id: UUID) -> bool:
        return await self.svc.check_closure_exists(parent_position_id, child_position_id)

    @audit_action(action="CLOSURE.DELETE", entity_type="PositionClosure")
    async def delete_position_closures_by_position(self, position_id: UUID, actor: User) -> int:
        try:
            deleted_count = await self.svc.delete_closures_by_position(position_id)
            logger.info("🗑️ Deleted {} closure records for position: {}", deleted_count, position_id)
            return deleted_count
        except Exception as e:
            logger.exception("❌ Failed to delete closure by position: {}", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")
