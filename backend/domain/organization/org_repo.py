from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from uuid import UUID
from sqlalchemy.exc import IntegrityError

from sqlmodel import select, and_, or_
from backend.core.DatabaseService.base import DatabaseService
from backend.core.DatabaseService.repositories import BaseRepository
from backend.domain.organization.models import (
    Organization, OrgUnit, Position, Assignment, ReportingLink, PositionClosure
)
from backend.domain.user.models import User
from backend.core.LoggingService import logger


# ============================================================
# ORGANIZATION REPOSITORY
# ============================================================

class OrganizationRepository(BaseRepository[Organization]):
    """Tashkilot ma'lumotlari bilan ishlash."""

    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Organization, db)

    async def get_org_unit_by_user_id_(self, user_id: UUID) -> Optional[UUID]:
        """Userga tegishli org unitni topadi (faol assignment orqali)."""
        async with self.db.session_scope() as session:
            stmt = (
                select(OrgUnit.id)
                .join(Position, Position.org_unit_id == OrgUnit.id)
                .join(Assignment, Assignment.position_id == Position.id)
                .where(
                    Assignment.user_id == user_id,
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                    Position.is_deleted == False,
                    OrgUnit.is_deleted == False
                )
                .limit(1)
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def create_organization(self, name: str, code: Optional[str], description: Optional[str]) -> Organization:
        org = Organization(name=name, code=code, description=description)
        return await self.create(org)

    async def get_by_code(self, code: str) -> Optional[Organization]:
        async with self.db.session_scope() as session:
            stmt = select(Organization).where(
                Organization.code == code,
                Organization.is_deleted == False
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_all(self) -> List[Organization]:
        async with self.db.session_scope() as session:
            stmt = select(Organization).where(Organization.is_deleted == False)
            res = await session.execute(stmt)
            return res.scalars().all()

    async def search(self, keyword: str) -> List[Organization]:
        async with self.db.session_scope() as session:
            stmt = select(Organization).where(
                and_(
                    Organization.is_deleted == False,
                    or_(
                        Organization.name.ilike(f"%{keyword}%"),
                        Organization.code.ilike(f"%{keyword}%")
                    ),
                )
            )
            res = await session.execute(stmt)
            return res.scalars().all()


# ============================================================
# ORG UNIT REPOSITORY
# ============================================================

class OrgUnitRepository(BaseRepository[OrgUnit]):
    """Bo‘linmalar (OrgUnit) bilan ishlash."""

    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(OrgUnit, db)

    async def create_unit(self, organization_id: UUID, name: str, unit_type: str,
                          parent_id: Optional[UUID] = None, order_no: int = 0) -> OrgUnit:
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

    async def get_active_position_by_user(self, user_id: UUID) -> Optional[UUID]:
        async with self.db.session_scope() as session:
            stmt = (
                select(Assignment.position_id)
                .where(
                    Assignment.user_id == user_id,
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False
                )
                .limit(1)
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_units_and_staff_for_user(self, user_id: UUID) -> Dict[str, Any]:
        today = date.today()
        async with self.db.session_scope() as session:

            # 1) foydalanuvchi pozitsiyalari
            stmt_my_pos = (
                select(Position.id, Position.org_unit_id)
                .join(Assignment, Assignment.position_id == Position.id)
                .where(
                    Assignment.user_id == user_id,
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                    Position.is_deleted == False,
                    or_(Assignment.valid_to.is_(None), Assignment.valid_to >= today),
                    Assignment.valid_from <= today,
                )
            )
            my_rows = (await session.execute(stmt_my_pos)).all()
            my_position_ids = {row[0] for row in my_rows}
            my_org_unit_ids = {row[1] for row in my_rows}

            # 2) closure (manager → subordinates)
            target_position_ids: set[UUID] = set()
            child_org_unit_ids: set[UUID] = set()

            if my_position_ids:
                stmt_children = (
                    select(PositionClosure.child_position_id, Position.org_unit_id)
                    .join(Position, Position.id == PositionClosure.child_position_id)
                    .where(
                        PositionClosure.parent_position_id.in_(my_position_ids),
                        PositionClosure.depth >= 1,
                        PositionClosure.is_deleted == False,
                        Position.is_deleted == False,
                    )
                )
                child_rows = (await session.execute(stmt_children)).all()
                target_position_ids = {r[0] for r in child_rows}
                child_org_unit_ids = {r[1] for r in child_rows}

            # 3) fallback — agar closure yo‘q
            if not target_position_ids and my_org_unit_ids:
                stmt_fb = select(Position.id).where(
                    Position.org_unit_id.in_(my_org_unit_ids),
                    Position.is_deleted == False
                )
                target_position_ids = set((await session.execute(stmt_fb)).scalars().all())
                child_org_unit_ids = set(my_org_unit_ids)

            if not target_position_ids:
                return {"units": [], "position_count": 0, "staff_count": 0}

            # 4) org_unitlar
            stmt_units = select(OrgUnit).where(
                OrgUnit.id.in_(list(child_org_unit_ids)),
                OrgUnit.is_deleted == False,
            )
            units = list((await session.execute(stmt_units)).scalars().all())

            # 5) staff
            stmt_staff = (
                select(User, Position, OrgUnit)
                .join(Assignment, Assignment.user_id == User.id)
                .join(Position, Position.id == Assignment.position_id)
                .join(OrgUnit, OrgUnit.id == Position.org_unit_id)
                .where(
                    Assignment.position_id.in_(list(target_position_ids)),
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                    or_(Assignment.valid_to.is_(None), Assignment.valid_to >= today),
                    Assignment.valid_from <= today,
                    User.is_deleted == False,
                    User.is_active == True,
                    Position.is_deleted == False,
                    OrgUnit.is_deleted == False,
                )
            )
            staff_rows = (await session.execute(stmt_staff)).all()

            unit_map: Dict[UUID, Dict[str, Any]] = {}
            for u in units:
                unit_map[u.id] = {
                    "unit": {"id": u.id, "name": u.name, "unit_type": u.unit_type},
                    "staff": [],
                }

            for user, pos, unit in staff_rows:
                unit_map.setdefault(unit.id, {
                    "unit": {"id": unit.id, "name": unit.name, "unit_type": unit.unit_type},
                    "staff": []
                })["staff"].append({
                    "id": user.id,
                    "full_name": user.full_name,
                    "username": user.username,
                    "position_title": pos.title,
                })

            staff_count = sum(len(u["staff"]) for u in unit_map.values())
            return {
                "units": list(unit_map.values()),
                "position_count": len(target_position_ids),
                "staff_count": staff_count,
            }

    async def get_org_unit_by_user_id(self, user_id: UUID) -> Optional[UUID]:
        async with self.db.session_scope() as session:
            stmt = (
                select(OrgUnit.id)
                .join(Position, Position.org_unit_id == OrgUnit.id)
                .join(Assignment, Assignment.position_id == Position.id)
                .where(Assignment.user_id == user_id)
                .limit(1)
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_all_by_org(self, organization_id: UUID) -> List[OrgUnit]:
        async with self.db.session_scope() as session:
            stmt = select(OrgUnit).where(
                OrgUnit.organization_id == organization_id,
                OrgUnit.is_deleted == False
            )
            res = await session.execute(stmt)
            return res.scalars().all()

    async def get_children(self, parent_id: UUID) -> List[OrgUnit]:
        async with self.db.session_scope() as session:
            stmt = select(OrgUnit).where(
                OrgUnit.parent_id == parent_id,
                OrgUnit.is_deleted == False
            )
            res = await session.execute(stmt)
            return res.scalars().all()

    async def get(self, id: UUID) -> Optional[OrgUnit]:
        async with self.db.session_scope() as session:
            stmt = select(OrgUnit).where(
                OrgUnit.id == id,
                OrgUnit.is_deleted == False
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_tree(self, organization_id: UUID) -> Dict:
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
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Position, db)

    async def create_position(self, org_unit_id: UUID, title: str,
                              is_unique: bool = True, quota: Optional[int] = None) -> Position:
        pos = Position(
            org_unit_id=org_unit_id,
            title=title,
            is_unique=is_unique,
            quota=quota
        )
        return await self.create(pos)

    async def get_position_list(self) -> List[Position]:
        return await self.list({"is_deleted": False})

    async def get_by_unit(self, org_unit_id: UUID) -> List[Position]:
        return await self.list({"org_unit_id": org_unit_id, "is_deleted": False})

    async def get_existing(self, org_unit_id: UUID, title: str) -> Optional[Position]:
        stmt = select(Position).where(
            Position.org_unit_id == org_unit_id,
            Position.title == title,
            Position.is_unique == True,
            Position.is_deleted == False,
        )
        return await self.db.one_or_none(stmt)

    async def get_by_user_id(self, position_id: UUID) -> Optional[Position]:
        async with self.db.session_scope() as session:
            stmt = (
                select(Position)
                .where(Position.id == position_id, Position.is_deleted == False)
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_positions_by_org_unit(self, org_unit_id: UUID) -> List[Position]:
        async with self.db.session_scope() as session:
            stmt = (
                select(Position)
                .where(
                    Position.org_unit_id == org_unit_id,
                    Position.is_deleted == False
                )
                .order_by(Position.order_no.asc(), Position.title.asc())
            )
            rows = await session.execute(stmt)
            return list(rows.scalars().all())


# ============================================================
# REPORTING LINK REPOSITORY
# ============================================================

class ReportingLinkRepository(BaseRepository[ReportingLink]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(ReportingLink, db)

    async def create_reporting_link(self, parent_position_id: UUID,
                                    child_position_id: UUID,
                                    relation_type: str = "LINE",
                                    meta: Optional[dict] = None) -> ReportingLink:
        link = ReportingLink(
            parent_position_id=parent_position_id,
            child_position_id=child_position_id,
            relation_type=relation_type,
            meta=meta,
        )
        return await self.create(link)

    async def get_by_parent(self, parent_position_id: UUID) -> List[ReportingLink]:
        return await self.list({"parent_position_id": parent_position_id, "is_deleted": False})

    async def get_by_child(self, child_position_id: UUID) -> List[ReportingLink]:
        return await self.list({"child_position_id": child_position_id, "is_deleted": False})

    async def get_direct_manager(self, child_position_id: UUID) -> Optional[ReportingLink]:
        stmt = select(ReportingLink).where(
            ReportingLink.child_position_id == child_position_id,
            ReportingLink.is_deleted == False
        )
        return await self.db.one_or_none(stmt)

    async def check_if_exists(self, parent_position_id: UUID,
                              child_position_id: UUID) -> Optional[ReportingLink]:
        stmt = select(ReportingLink).where(
            ReportingLink.parent_position_id == parent_position_id,
            ReportingLink.child_position_id == child_position_id,
            ReportingLink.is_deleted == False
        )
        return await self.db.one_or_none(stmt)

    async def list_all_active(self) -> List[ReportingLink]:
        return await self.list({"is_deleted": False})


# ============================================================
# ASSIGNMENT REPOSITORY
# ============================================================

class AssignmentRepository(BaseRepository[Assignment]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Assignment, db)

    async def get_by_user(self, user_id: UUID) -> List[Assignment]:
        return await self.list({"user_id": user_id, "is_deleted": False})

    async def list_assignments(self) -> List[Assignment]:
        return await self.list()

    async def get_by_position(self, position_id: UUID) -> List[Assignment]:
        return await self.list({"position_id": position_id, "is_deleted": False})

    # --- mavjud ACTIVE assignmentni yopish (position bo‘yicha)
    async def terminate_active_by_position(
        self,
        position_id: UUID,
        *,
        terminated_at: date | None = None
    ) -> int:
        terminated_at = terminated_at or date.today()

        async with self.db.session_scope() as session:
            stmt = (
                select(Assignment)
                .where(
                    Assignment.position_id == position_id,
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                )
                .with_for_update()
            )
            rows = (await session.execute(stmt)).scalars().all()

            for a in rows:
                a.status = "TERMINATED"
                a.valid_to = terminated_at
                a.updated_at = datetime.utcnow()
                session.add(a)

            return len(rows)

    # --- userning barcha ACTIVE assignmentlarini yopish
    async def terminate_active_by_user(
        self,
        user_id: UUID,
        *,
        terminated_at: date | None = None
    ) -> int:
        terminated_at = terminated_at or date.today()

        async with self.db.session_scope() as session:
            stmt = (
                select(Assignment)
                .where(
                    Assignment.user_id == user_id,
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                )
                .with_for_update()
            )
            rows = (await session.execute(stmt)).scalars().all()

            for a in rows:
                a.status = "TERMINATED"
                a.valid_to = terminated_at
                a.updated_at = datetime.utcnow()
                session.add(a)

            return len(rows)

    # --- position bo‘yicha ACTIVE assignment (lock bilan)
    async def get_active_by_position_for_update(
        self,
        position_id: UUID
    ) -> Optional[Assignment]:
        async with self.db.session_scope() as session:
            stmt = (
                select(Assignment)
                .where(
                    Assignment.position_id == position_id,
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                )
                .with_for_update()
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def check_active_assignment(self, position_id: UUID) -> Optional[Assignment]:
        stmt = select(Assignment).where(
            Assignment.position_id == position_id,
            Assignment.status == "ACTIVE",
            Assignment.is_deleted == False
        )
        return await self.db.one_or_none(stmt)

    async def get_active_user_ids_by_unit(self, unit_id: UUID) -> List[UUID]:
        today = date.today()
        async with self.db.session_scope() as session:
            stmt = (
                select(Assignment.user_id)
                .join(Position, Position.id == Assignment.position_id)
                .where(
                    Position.org_unit_id == unit_id,
                    Position.is_deleted == False,
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                    Assignment.valid_from <= today,
                    ((Assignment.valid_to.is_(None)) | (Assignment.valid_to >= today))
                )
            )
            rows = (await session.execute(stmt)).scalars().all()
            seen, out = set(), []
            for uid in rows:
                if uid not in seen:
                    seen.add(uid)
                    out.append(uid)
            return out

    async def get_active_titles_for_users(self, user_ids: List[UUID]) -> List[Tuple[UUID, str]]:
        if not user_ids:
            return []
        today = date.today()
        async with self.db.session_scope() as session:
            stmt = (
                select(Assignment.user_id, Position.title)
                .join(Position, Position.id == Assignment.position_id)
                .where(
                    Assignment.user_id.in_(user_ids),
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                    Position.is_deleted == False,
                    Assignment.valid_from <= today,
                    ((Assignment.valid_to.is_(None)) | (Assignment.valid_to >= today))
                )
            )
            rows = (await session.execute(stmt)).all()
            title_map: Dict[UUID, str] = {}
            for uid, title in rows:
                if uid not in title_map:
                    title_map[uid] = title
            return list(title_map.items())

    async def get_users_by_subordinates(self, user_id: UUID) -> list[UUID]:
        today = date.today()
        async with self.db.session_scope() as session:
            pos_stmt = (
                select(Assignment.position_id)
                .where(
                    Assignment.user_id == user_id,
                    Assignment.status == "ACTIVE",
                    Assignment.valid_from <= today,
                    ((Assignment.valid_to.is_(None)) | (Assignment.valid_to >= today))
                )
            )
            current_positions = (await session.execute(pos_stmt)).scalars().all()
            if not current_positions:
                return []

            pos_tree = (
                select(PositionClosure.child_position_id)
                .join(Position, Position.id == PositionClosure.child_position_id)
                .where(
                    PositionClosure.parent_position_id.in_(current_positions),
                    PositionClosure.depth >= 0,
                    Position.is_deleted == False
                )
            )
            subordinate_positions = (await session.execute(pos_tree)).scalars().all()
            if not subordinate_positions:
                return []

            stmt = (
                select(Assignment.user_id)
                .where(
                    Assignment.position_id.in_(subordinate_positions),
                    Assignment.status == "ACTIVE",
                    Assignment.valid_from <= today,
                    ((Assignment.valid_to.is_(None)) | (Assignment.valid_to >= today))
                )
            )
            users = (await session.execute(stmt)).scalars().all()
            return list(set(users))

    async def get_users_by_positions(self, position_ids: List[UUID]) -> List[UUID]:
        async with self.db.session_scope() as session:
            stmt = (
                select(Assignment.user_id)
                .where(
                    Assignment.position_id.in_(position_ids),
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False
                )
            )
            rows = await session.execute(stmt)
            return [r[0] for r in rows.all()]

    async def create_assignment(self, user_id: UUID,
                               position_id: UUID,
                               valid_from: date,
                               valid_to: Optional[date] = None,
                               status: str = "ACTIVE") -> Assignment:
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

    # -----------------------------
    # Ichki yordamchilar (faqat shu sessiya ichida ishlatamiz)
    # -----------------------------
    async def _exists(
        self,
        session,
        parent_position_id: UUID,
        child_position_id: UUID
    ) -> bool:
        stmt = select(PositionClosure).where(
            and_(
                PositionClosure.parent_position_id == parent_position_id,
                PositionClosure.child_position_id == child_position_id,
                PositionClosure.is_deleted == False,
            )
        )
        return (await session.execute(stmt)).scalar_one_or_none() is not None

    async def _get_by_child(self, session, child_position_id: UUID) -> List[PositionClosure]:
        stmt = select(PositionClosure).where(
            and_(
                PositionClosure.child_position_id == child_position_id,
                PositionClosure.is_deleted == False,
            )
        )
        return list((await session.execute(stmt)).scalars().all())

    # ------------------------------------------------------------
    # Yagona closure yaratish (race-safe)
    # ------------------------------------------------------------
    async def create_closure(
        self,
        parent_position_id: UUID,
        child_position_id: UUID,
        depth: int = 1
    ) -> PositionClosure:
        """
        Ierarxik bog‘liqlikni yaratadi (masalan, bevosita yoki bilvosita rahbar).
        Atomar va dublikatlarga chidamli.
        """
        async with self.db.session_scope() as session:
            # Mavjudligini aynan shu sessiyada tekshiramiz (race-safe)
            if await self._exists(session, parent_position_id, child_position_id):
                stmt = select(PositionClosure).where(
                    and_(
                        PositionClosure.parent_position_id == parent_position_id,
                        PositionClosure.child_position_id == child_position_id,
                        PositionClosure.is_deleted == False,
                    )
                )
                return (await session.execute(stmt)).scalar_one()  # mavjudini qaytaramiz

            closure = PositionClosure(
                parent_position_id=parent_position_id,
                child_position_id=child_position_id,
                depth=depth,
            )
            session.add(closure)
            try:
                await session.flush()
            except IntegrityError:
                # Unique constraint bo‘lsa: parallel insertda dublikatdan qo‘rqmaymiz
                logger.debug("PositionClosure duplicate detected during create_closure; returning existing.")
                stmt = select(PositionClosure).where(
                    and_(
                        PositionClosure.parent_position_id == parent_position_id,
                        PositionClosure.child_position_id == child_position_id,
                        PositionClosure.is_deleted == False,
                    )
                )
                return (await session.execute(stmt)).scalar_one()
            await session.refresh(closure)
            return closure

    async def get_child_positions(self, parent_position_id: UUID) -> List[UUID]:
        async with self.db.session_scope() as session:
            stmt = (
                select(PositionClosure.child_position_id)
                .where(
                    and_(
                        PositionClosure.parent_position_id == parent_position_id,
                        PositionClosure.is_deleted == False,
                    )
                )
            )
            res = await session.execute(stmt)
            return [row[0] for row in res.all()]

    # ------------------------------------------------------------
    # Ko‘p sonli closurelarni bulk tarzda yaratish
    # (Agar sizda allaqachon yig‘ilgan ORM obyektlar bo‘lsa, ishlating)
    # ------------------------------------------------------------
    async def bulk_create_closures(self, closures: List[PositionClosure]) -> List[PositionClosure]:
        # BaseRepository.bulk_create() ichida session_scope ishlaydi
        return await self.bulk_create(closures)

    # ------------------------------------------------------------
    # Rekursiv ierarxiyani avtomatik kiritish (atomar tranzaksiya)
    # ------------------------------------------------------------
    async def insert_closure(self, child_id: UUID, parent_id: Optional[UUID]) -> None:
        """
        self-loop (depth=0) + parent (depth=1) + barcha ajdodlar → child
        Hammasi bitta tranzaksiya/sessiyada bajariladi (connection leak yo‘q).
        """
        async with self.db.session_scope() as session:
            to_add: List[PositionClosure] = []

            # ✅ 1) Self reference (child → child, depth=0)
            if not await self._exists(session, child_id, child_id):
                to_add.append(PositionClosure(
                    parent_position_id=child_id,
                    child_position_id=child_id,
                    depth=0
                ))

            # ✅ 2) Root bo‘lsa — faqat self closure
            if not parent_id:
                if to_add:
                    session.add_all(to_add)
                    try:
                        await session.flush()
                    except IntegrityError:
                        logger.debug("Duplicates detected during insert_closure self-insert; safe to ignore.")
                return

            # ✅ 3) Direct parent → child (depth = 1)
            if not await self._exists(session, parent_id, child_id):
                to_add.append(PositionClosure(
                    parent_position_id=parent_id,
                    child_position_id=child_id,
                    depth=1
                ))

            # ✅ 4) Parentning barcha ajdodlari → child
            parent_ancestors = await self._get_by_child(session, parent_id)
            for ancestor in parent_ancestors:
                # Parentning self-loopini ikki marta qo‘ymaslik
                if (
                    ancestor.parent_position_id == parent_id
                    and ancestor.child_position_id == parent_id
                    and ancestor.depth == 0
                ):
                    continue

                if not await self._exists(session, ancestor.parent_position_id, child_id):
                    to_add.append(PositionClosure(
                        parent_position_id=ancestor.parent_position_id,
                        child_position_id=child_id,
                        depth=ancestor.depth + 1
                    ))

            # ✅ 5) Bulk insert (shu sessiyada). Dublikatlarga chidamli.
            if to_add:
                session.add_all(to_add)
                try:
                    await session.flush()
                except IntegrityError:
                    logger.debug("Duplicates detected during insert_closure bulk flush; safe to ignore.")

    # ------------------------------------------------------------
    # Yordamchi funksiyalar (public)
    # ------------------------------------------------------------
    async def get_by_parent(self, parent_position_id: UUID) -> List[PositionClosure]:
        return await self.list({
            "parent_position_id": parent_position_id,
            "is_deleted": False
        })

    async def get_by_child(self, child_position_id: UUID) -> List[PositionClosure]:
        return await self.list({
            "child_position_id": child_position_id,
            "is_deleted": False
        })

    async def get_direct_chain(self, child_position_id: UUID) -> Optional[PositionClosure]:
        stmt = select(PositionClosure).where(
            and_(
                PositionClosure.child_position_id == child_position_id,
                PositionClosure.depth == 1,
                PositionClosure.is_deleted == False
            )
        )
        # db.one_or_none() o‘zi session_scope ochadi → OK
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
        """
        Lavozim o‘chirildi deb hisoblanib, unga tegishli barcha closure yozuvlarini butunlay o‘chiradi.
        Eslatma: sizning DatabaseService.delete_many() haqiqiy DELETE qiladi (soft emas).
        Agar soft-delete kerak bo‘lsa, alohida soft_delete_many() dan foydalansangiz bo‘ladi.
        """
        return await self.db.delete_many(PositionClosure, {"parent_position_id": position_id})