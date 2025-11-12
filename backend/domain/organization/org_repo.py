from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from uuid import UUID

from sqlmodel import select, and_, or_
from backend.core.DatabaseService.base import DatabaseService
from backend.core.DatabaseService.repositories import BaseRepository
from backend.domain.organization.models import (
    Organization, OrgUnit, Position, Assignment, ReportingLink, PositionClosure
)
from backend.domain.user.models import User


# ============================================================
# ORGANIZATION REPOSITORY
# ============================================================

class OrganizationRepository(BaseRepository[Organization]):
    """Tashkilot (Organization) ma'lumotlari bilan ishlovchi qatlam.
    Maqsad: CRUD, qidiruv, mavjudligini tekshirish, kod bo‘yicha olish.
    """

    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(Organization, db)

    async def get_org_unit_by_user_id_(self, user_id: UUID) -> Optional[UUID]:
        """
        Userning faol assignment'i orqali unga tegishli OrgUnit (bo'lim) ID sini topadi.
        return: OrgUnit ID (yoki None)
        """

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
                    OrgUnit.is_deleted == False,
                )
                .limit(1)
            )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

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
    """Tashkilot ichidagi bo‘linmalar (fakultet, markaz, bo‘lim) bilan ishlash.

    Yangi: rahbar foydalanuvchi (prorektor, bo'lim boshlig'i va h.k.) tizimga kirganda,
    unga tegishli bo'linmalar va shu bo'linmalardagi ishchi xodimlarni qaytaruvchi yordamchi metod.
    """

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
        """
        Berilgan foydalanuvchi (rahbar) uchun ko'rinish doirasidagi bo'linmalar va xodimlar ro'yxatini qaytaradi.

        Qoidalar:
        - Foydalanuvchining faol assignmentlari orqali uning position(lar)i olinadi.
        - Agar PositionClosure jadvalida ushbu position(lar) parent sifatida mavjud bo'lsa,
          barcha child position(lar) (depth >= 1) boshqaruv ostida deb qabul qilinadi.
        - Agar PositionClosure topilmasa (fallback), foydalanuvchining o'zi biriktirilgan org_unit(lar) dagi
          barcha position(lar) olinadi (bo'lim boshlig'i ssenariysi uchun mos).
        - Shu target position(lar) bo'yicha ACTIVE assignment'li foydalanuvchilar olinadi.

        Natija struktura:
        {
            "units": [
                {
                    "unit": {"id": UUID, "name": str, "unit_type": str},
                    "staff": [
                        {"id": UUID, "full_name": str | None, "username": str, "position_title": str | None}
                    ]
                }, ...
            ],
            "position_count": int,
            "staff_count": int
        }
        """
        today = date.today()
        async with self.db.session_scope() as session:
            # 1) Foydalanuvchining faol position(lar)i
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
            res_my_pos = await session.execute(stmt_my_pos)
            rows = res_my_pos.all()
            my_position_ids = {r[0] for r in rows}
            my_org_unit_ids = {r[1] for r in rows}

            target_position_ids: set[UUID] = set()

            if my_position_ids:
                # 2) PositionClosure orqali bo'ysinuvchi position(lar)
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
                res_children = await session.execute(stmt_children)
                child_rows = res_children.all()
                target_position_ids = {r[0] for r in child_rows}
                child_org_unit_ids = {r[1] for r in child_rows}
            else:
                child_org_unit_ids = set()

            # 3) Agar closure topilmagan bo'lsa, fallback: o'z org_unit(lar)idagi barcha position(lar)
            if not target_position_ids and my_org_unit_ids:
                stmt_fallback_pos = select(Position.id).where(
                    Position.org_unit_id.in_(my_org_unit_ids),
                    Position.is_deleted == False,
                )
                res_fb = await session.execute(stmt_fallback_pos)
                target_position_ids = set(res_fb.scalars().all())
                child_org_unit_ids = set(my_org_unit_ids)

            # Hech narsa topilmasa, bo'sh natija
            if not target_position_ids:
                return {"units": [], "position_count": 0, "staff_count": 0}

            # 4) Target org_unitlar obyektlari
            unit_ids = list(child_org_unit_ids)
            stmt_units = select(OrgUnit).where(OrgUnit.id.in_(unit_ids), OrgUnit.is_deleted == False)
            res_units = await session.execute(stmt_units)
            units = list(res_units.scalars().all())

            # 5) Target position(lar) bo'yicha ACTIVE assignmentlar va foydalanuvchilar
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
            res_staff = await session.execute(stmt_staff)
            staff_rows = res_staff.all()

            # 6) Natijani yig'ish
            unit_map: Dict[UUID, Dict[str, Any]] = {}
            for u in units:
                unit_map[u.id] = {
                    "unit": {"id": u.id, "name": u.name, "unit_type": u.unit_type},
                    "staff": [],
                }

            for u, pos, ou in staff_rows:
                entry = {
                    "id": u.id,
                    "full_name": u.full_name,
                    "username": u.username,
                    "position_title": pos.title,
                }
                if ou.id not in unit_map:
                    unit_map[ou.id] = {
                        "unit": {"id": ou.id, "name": ou.name, "unit_type": ou.unit_type},
                        "staff": [entry],
                    }
                else:
                    unit_map[ou.id]["staff"].append(entry)

            staff_count = sum(len(v["staff"]) for v in unit_map.values())

            return {
                "units": list(unit_map.values()),
                "position_count": len(target_position_ids),
                "staff_count": staff_count,
            }

    async def get_org_unit_by_user_id(self, user_id: UUID) -> Optional[UUID]:
        """
        Foydalanuvchi qaysi org_unitga tegishliligini assignment → position → org_unit orqali aniqlaydi
        """

        async with self.db.session_scope() as session:
            stmt = (
                select(OrgUnit.id)
                .join(Position, Position.org_unit_id == OrgUnit.id)
                .join(Assignment, Assignment.position_id == Position.id)
                .where(
                    Assignment.user_id == user_id,
                )
                .limit(1)
            )

            res = await session.execute(stmt)
            org_unit_id = res.scalar_one_or_none()
            return org_unit_id

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
            result = await session.execute(stmt)
            return list(result.scalars().all())


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
            # unique preserve order
            seen, out = set(), []
            for uid in rows:
                if uid not in seen:
                    seen.add(uid)
                    out.append(uid)
            return out

    async def get_active_titles_for_users(self, user_ids: List[UUID]) -> List[Tuple[UUID, str]]:
        """User → birlamchi (birinchi topilgan) lavozim nomi."""
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
            # user_id -> first title
            title_map: Dict[UUID, str] = {}
            for uid, title in rows:
                if uid not in title_map:
                    title_map[uid] = title
            return list(title_map.items())

    async def get_users_by_subordinates(self, user_id: UUID) -> list[UUID]:
        today = date.today()

        async with self.db.session_scope() as session:
            # Select current user's position
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

            # ✅ Get subordinate positions via PositionClosure
            pos_tree = (
                select(PositionClosure.child_position_id)
                .join(Position, Position.id == PositionClosure.child_position_id)
                .where(
                    PositionClosure.parent_position_id.in_(current_positions),
                    PositionClosure.depth >= 0,  # ✅ self + subordinates
                    Position.is_deleted == False
                )
            )

            subordinate_positions = (await session.execute(pos_tree)).scalars().all()

            if not subordinate_positions:
                return []

            # ✅ Get users of those positions
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

            return list(set(users))  # unique users

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
            res = await session.execute(stmt)
            return [r[0] for r in res.all()]

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

    async def get_child_positions(self, parent_position_id: UUID) -> List[UUID]:
        async with self.db.session_scope() as session:
            stmt = (
                select(PositionClosure.child_position_id)
                .where(PositionClosure.parent_position_id == parent_position_id)
            )
            res = await session.execute(stmt)
            return [r[0] for r in res.all()]

    # ------------------------------------------------------------
    # Ko‘p sonli closurelarni bulk tarzda yaratish
    # ------------------------------------------------------------
    async def bulk_create_closures(self, closures: list[PositionClosure]) -> list[PositionClosure]:
        return await self.bulk_create(closures)

    # ------------------------------------------------------------
    # Rekursiv ierarxiyani avtomatik kiritish (asosiy funksiya)
    # ------------------------------------------------------------
    async def insert_closure(self, child_id: UUID, parent_id: Optional[UUID]):
        closures: list[PositionClosure] = []

        # ✅ 1) Always add self reference (child → child, depth=0)
        if not await self.check_if_exists(child_id, child_id):
            closures.append(PositionClosure(
                parent_position_id=child_id,
                child_position_id=child_id,
                depth=0
            ))

        # ✅ 2) Root node bo‘lsa — faqat self closure
        if not parent_id:
            if closures:
                await self.bulk_create(closures)
            return

        # ✅ 3) Direct parent → child (depth = 1)
        if not await self.check_if_exists(parent_id, child_id):
            closures.append(PositionClosure(
                parent_position_id=parent_id,
                child_position_id=child_id,
                depth=1
            ))

        # ✅ 4) Parentning barcha ajdodlari → child
        parent_ancestors = await self.get_by_child(parent_id)

        for ancestor in parent_ancestors:
            if ancestor.parent_position_id == parent_id and ancestor.child_position_id == parent_id:
                # skip parent's self loop to avoid duplicate
                continue

            exists = await self.check_if_exists(ancestor.parent_position_id, child_id)
            if not exists:
                closures.append(PositionClosure(
                    parent_position_id=ancestor.parent_position_id,
                    child_position_id=child_id,
                    depth=ancestor.depth + 1
                ))

        # ✅ 5) Bulk insert with safety
        if closures:
            try:
                await self.bulk_create(closures)
            except Exception as e:
                # 💡 Ignore duplicates silently (race-safe)
                pass

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
