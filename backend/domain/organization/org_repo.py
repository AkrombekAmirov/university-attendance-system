from __future__ import annotations
from typing import List, Optional, Dict
from datetime import date
from uuid import UUID

from sqlmodel import select, and_, or_
from backend.core.DatabaseService.base import DatabaseService
from backend.core.DatabaseService.repositories import BaseRepository
from backend.domain.organization.models import (
    Organization, OrgUnit, Position, Assignment, ReportingLink, PositionClosure
)


# ============================================================
# ORGANIZATION REPOSITORY
# ============================================================

class OrganizationRepository(BaseRepository[Organization]):
    """Tashkilot (Organization) ma'lumotlari bilan ishlovchi qatlam.
    Maqsad: CRUD, qidiruv, mavjudligini tekshirish, kod bo‘yicha olish.
    """

    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Organization, db)

    async def create_organization(self, name: str, code: Optional[str], description: Optional[str]) -> Organization:
        org = Organization(name=name, code=code, description=description)
        return await self.create(org)

    async def get_by_code(self, code: str) -> Optional[Organization]:
        """Kod bo‘yicha tashkilotni olish (unique)."""
        async with self.db.session_scope() as session:
            stmt = select(Organization).where(Organization.code == code, Organization.is_deleted == False)
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_all(self) -> List[Organization]:
        """Barcha faol tashkilotlarni olish."""
        async with self.db.session_scope() as session:
            stmt = select(Organization).where(Organization.is_deleted == False)
            res = await session.execute(stmt)
            return res.scalars().all()

    async def search(self, keyword: str) -> List[Organization]:
        """Nom yoki kod bo‘yicha qidiruv."""
        async with self.db.session_scope() as session:
            stmt = select(Organization).where(
                and_(Organization.is_deleted == False,
                     or_(Organization.name.ilike(f"%{keyword}%"),
                         Organization.code.ilike(f"%{keyword}%")))
            )
            res = await session.execute(stmt)
            return res.scalars().all()


# ============================================================
# ORG UNIT REPOSITORY
# ============================================================

class OrgUnitRepository(BaseRepository[OrgUnit]):
    """Tashkilot ichidagi bo‘linmalar (fakultet, markaz, bo‘lim) bilan ishlash."""

    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(OrgUnit, db)

    async def create_unit(self, organization_id: UUID, name: str, unit_type: str,
                          parent_id: Optional[UUID] = None, order_no: int = 0) -> OrgUnit:
        """Bo‘linma yaratish (parent bo‘lsa path orqali daraxt hosil qiladi)."""
        parent_path = "/"
        if parent_id:
            parent = await self.get_by_id(parent_id)
            parent_path = f"{parent.path or '/'}{parent.id}/"

        unit = OrgUnit(
            organization_id=organization_id,
            name=name,
            unit_type=unit_type,
            parent_id=parent_id,
            path=parent_path,
            order_no=order_no,
        )
        created = await self.create(unit)
        created.path = f"{parent_path}{created.id}/"
        await self.update(created)
        return created

    async def get_all_by_org(self, organization_id: UUID) -> List[OrgUnit]:
        """Tashkilot bo‘yicha barcha bo‘linmalarni olish."""
        async with self.db.session_scope() as session:
            stmt = select(OrgUnit).where(OrgUnit.organization_id == organization_id, OrgUnit.is_deleted == False)
            res = await session.execute(stmt)
            return res.scalars().all()

    async def get_children(self, parent_id: UUID) -> List[OrgUnit]:
        """Berilgan bo‘linmaga to‘g‘ridan‑to‘g‘ri bo‘ysunuvchi bo‘linmalar."""
        async with self.db.session_scope() as session:
            stmt = select(OrgUnit).where(OrgUnit.parent_id == parent_id, OrgUnit.is_deleted == False)
            res = await session.execute(stmt)
            return res.scalars().all()

    async def get(self, id: UUID):
        async with self.db.session_scope() as session:
            stmt = select(OrgUnit).where(OrgUnit.id == id, OrgUnit.is_deleted == False)
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_tree(self, organization_id: UUID) -> Dict:
        """Bo‘linmalar daraxtini JSON formatida qaytaradi."""
        units = await self.get_all_by_org(organization_id)
        mapping = {u.id: {"id": u.id, "name": u.name, "unit_type": u.unit_type, "children": []} for u in units}
        roots = []
        for u in units:
            if u.parent_id and u.parent_id in mapping:
                mapping[u.parent_id]["children"].append(mapping[u.id])
            else:
                roots.append(mapping[u.id])
        return {"organization_id": organization_id, "tree": roots}


# ============================================================
# POSITION REPOSITORY
# ============================================================

class PositionRepository(BaseRepository[Position]):
    """Bo‘linma ichidagi aniq lavozimlar bilan ishlash."""

    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Position, db)

    async def create_position(self, org_unit_id: UUID,
                              title: str,
                              is_unique: bool = True,
                              quota: Optional[int] = None) -> Position:
        pos = Position(
            org_unit_id=org_unit_id,
            title=title,
            is_unique=is_unique,
            quota=quota
        )
        return await self.create(pos)

    async def get_position_list(self) -> List[Position]:
        """Barcha postionlarni get qilish"""
        return await self.list({"is_deleted": False})

    async def get_by_unit(self, org_unit_id: UUID) -> List[Position]:
        """Bo‘linmaga tegishli lavozimlarni olish."""
        return await self.list({"org_unit_id": org_unit_id, "is_deleted": False})

    async def get_existing(self, org_unit_id: UUID, title: str) -> Optional[Position]:
        """Yagona lavozim nomi bo‘linma ichida allaqachon mavjudligini tekshiradi."""
        stmt = select(Position).where(
            Position.org_unit_id == org_unit_id,
            Position.title == title,
            Position.is_unique == True,
            Position.is_deleted == False,
        )
        return await self.db.one_or_none(stmt)

    async def get_by_user_id(self, position_id: UUID) -> Optional[Position]:
        async with self.db.session_scope() as session:
            stmt = select(Position).where(Position.id == position_id, Position.is_deleted == False)
            res = await session.execute(stmt)
            return res.scalar_one_or_none()


# ============================================================
# REPORTING LINK REPOSITORY
# ============================================================
class ReportingLinkRepository(BaseRepository[ReportingLink]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(ReportingLink, db)

    async def create_reporting_link(
            self,
            parent_position_id: UUID,
            child_position_id: UUID,
            relation_type: str = "LINE",
            meta: Optional[dict] = None
    ) -> ReportingLink:
        """Yangi rahbar-xodim (parent-child) munosabatini yaratadi."""
        link = ReportingLink(
            parent_position_id=parent_position_id,
            child_position_id=child_position_id,
            relation_type=relation_type,
            meta=meta,
        )
        return await self.create(link)

    async def get_by_parent(self, parent_position_id: UUID) -> List[ReportingLink]:
        """Muayyan rahbarga biriktirilgan barcha bo‘ysinuvchi lavozimlarni oladi."""
        return await self.list({
            "parent_position_id": parent_position_id,
            "is_deleted": False
        })

    async def get_by_child(self, child_position_id: UUID) -> List[ReportingLink]:
        """Muayyan bo‘ysinuvchi lavozimni qaysi rahbarlarga bog‘langanligini oladi."""
        return await self.list({
            "child_position_id": child_position_id,
            "is_deleted": False
        })

    async def get_direct_manager(self, child_position_id: UUID) -> Optional[ReportingLink]:
        """Lavozimga biriktirilgan asosiy rahbarni oladi."""
        stmt = select(ReportingLink).where(
            ReportingLink.child_position_id == child_position_id,
            ReportingLink.is_deleted == False
        )
        return await self.db.one_or_none(stmt)

    async def check_if_exists(
            self,
            parent_position_id: UUID,
            child_position_id: UUID
    ) -> Optional[ReportingLink]:
        """Aynan shu bog‘lanish mavjud yoki yo‘qligini tekshiradi."""
        stmt = select(ReportingLink).where(
            ReportingLink.parent_position_id == parent_position_id,
            ReportingLink.child_position_id == child_position_id,
            ReportingLink.is_deleted == False
        )
        return await self.db.one_or_none(stmt)

    # async def delete_link(
    #     self,
    #     parent_position_id: UUID,
    #     child_position_id: UUID,
    #     hard: bool = False
    # ) -> bool:
    #     """Bog‘lanishni soft/hard delete qiladi."""
    #     async with self.db.session_scope() as session:
    #         if hard:
    #             stmt = delete(ReportingLink).where(
    #                 and_(
    #                     ReportingLink.parent_position_id == parent_position_id,
    #                     ReportingLink.child_position_id == child_position_id
    #                 )
    #             )
    #             await session.execute(stmt)
    #         else:
    #             stmt = select(ReportingLink).where(
    #                 ReportingLink.parent_position_id == parent_position_id,
    #                 ReportingLink.child_position_id == child_position_id,
    #                 ReportingLink.is_deleted == False
    #             )
    #             obj = await self.db.one_or_none(stmt)
    #             if obj:
    #                 obj.is_deleted = True
    #                 session.add(obj)
    #         await session.commit()
    #         return True

    async def list_all_active(self) -> List[ReportingLink]:
        """Barcha faol (soft delete bo‘lmagan) reporting linklarni qaytaradi."""
        return await self.list({"is_deleted": False})


class AssignmentRepository(BaseRepository[Assignment]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Assignment, db)

    async def get_by_user(self, user_id: UUID) -> List[Assignment]:
        return await self.list({"user_id": user_id, "is_deleted": False})

    async def list_assignments(self) -> List[Assignment]:
        return await self.list()

    async def get_by_position(self, position_id: UUID) -> List[Assignment]:
        return await self.list({"position_id": position_id, "is_deleted": False})

    async def check_active_assignment(self, position_id: UUID) -> Optional[Assignment]:
        stmt = select(Assignment).where(
            Assignment.position_id == position_id,
            Assignment.status == "ACTIVE",
            Assignment.is_deleted == False
        )
        return await self.db.one_or_none(stmt)

    async def create_assignment(
            self,
            user_id: UUID,
            position_id: UUID,
            valid_from: date,
            valid_to: Optional[date] = None,
            status: str = "ACTIVE"
    ) -> Assignment:
        """Yangi assignmentni DB ga yozadi."""
        async with self.db.session_scope() as session:
            assignment = Assignment(
                user_id=user_id,
                position_id=position_id,
                valid_from=valid_from,
                valid_to=valid_to,
                status=status,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)
            return assignment


class PositionClosureRepository(BaseRepository[PositionClosure]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(PositionClosure, db)

    # ------------------------------------------------------------
    # Yagona closure yaratish
    # ------------------------------------------------------------
    async def create_closure(
            self,
            parent_position_id: UUID,
            child_position_id: UUID,
            depth: int = 1
    ) -> PositionClosure:
        """
        Ierarxik bog‘liqlikni yaratadi (masalan, bevosita yoki bilvosita rahbar).
        """
        exists = await self.check_if_exists(parent_position_id, child_position_id)
        if exists:
            return exists  # dublikatni oldini oladi

        closure = PositionClosure(
            parent_position_id=parent_position_id,
            child_position_id=child_position_id,
            depth=depth,
        )
        return await self.create(closure)

    # ------------------------------------------------------------
    # Ko‘p sonli closurelarni bulk tarzda yaratish
    # ------------------------------------------------------------
    async def bulk_create_closures(self, closures: list[PositionClosure]) -> list[PositionClosure]:
        return await self.bulk_create(closures)

    # ------------------------------------------------------------
    # Rekursiv ierarxiyani avtomatik kiritish (asosiy funksiya)
    # ------------------------------------------------------------
    async def insert_closure(
            self,
            child_id: UUID,
            parent_id: UUID,
            created_by: Optional[UUID] = None
    ) -> list[PositionClosure]:
        """
        Yangi child lavozim uchun barcha parent chain asosida closure yozuvlarini yaratadi.
        Har bir parent uchun depth += 1 qilib qo‘shiladi.
        """
        closures_to_create: list[PositionClosure] = []

        # 1️⃣ Avval parent_id uchun mavjud barcha yuqori parentlarni olamiz
        parent_chain = await self.get_by_child(parent_id)

        # 2️⃣ Har bir yuqori parent uchun yangi yozuv (child_id uchun)
        for closure in parent_chain:
            exists = await self.check_if_exists(closure.parent_position_id, child_id)
            if not exists:
                closures_to_create.append(
                    PositionClosure(
                        parent_position_id=closure.parent_position_id,
                        child_position_id=child_id,
                        depth=closure.depth + 1,
                        created_by=created_by,
                    )
                )

        # 3️⃣ Bevosita parent uchun (depth = 1)
        direct_exists = await self.check_if_exists(parent_id, child_id)
        if not direct_exists:
            closures_to_create.append(
                PositionClosure(
                    parent_position_id=parent_id,
                    child_position_id=child_id,
                    depth=1,
                    created_by=created_by,
                )
            )

        # 4️⃣ O‘zi uchun yozuv (reflexive node, depth = 0)
        self_exists = await self.check_if_exists(child_id, child_id)
        if not self_exists:
            closures_to_create.append(
                PositionClosure(
                    parent_position_id=child_id,
                    child_position_id=child_id,
                    depth=0,
                    created_by=created_by,
                )
            )

        # 5️⃣ Bulk insert orqali bazaga kiritamiz
        if closures_to_create:
            await self.bulk_create(closures_to_create)

        return closures_to_create

    # ------------------------------------------------------------
    # Yordamchi funksiyalar
    # ------------------------------------------------------------
    async def get_by_parent(self, parent_position_id: UUID) -> list[PositionClosure]:
        return await self.list({
            "parent_position_id": parent_position_id,
            "is_deleted": False
        })

    async def get_by_child(self, child_position_id: UUID) -> list[PositionClosure]:
        return await self.list({
            "child_position_id": child_position_id,
            "is_deleted": False
        })

    async def get_direct_chain(self, child_position_id: UUID) -> Optional[PositionClosure]:
        stmt = select(PositionClosure).where(
            PositionClosure.child_position_id == child_position_id,
            PositionClosure.depth == 1,
            PositionClosure.is_deleted == False
        )
        return await self.db.one_or_none(stmt)

    async def check_if_exists(
            self,
            parent_position_id: UUID,
            child_position_id: UUID
    ) -> Optional[PositionClosure]:
        stmt = select(PositionClosure).where(
            and_(
                PositionClosure.parent_position_id == parent_position_id,
                PositionClosure.child_position_id == child_position_id,
                PositionClosure.is_deleted == False
            )
        )
        return await self.db.one_or_none(stmt)

    async def delete_closure_by_position(self, position_id: UUID) -> int:
        """Lavozim o‘chirildi deb hisoblanib, unga tegishli barcha closure yozuvlarini soft delete qiladi."""
        return await self.db.delete_many(PositionClosure, {"parent_position_id": position_id})
