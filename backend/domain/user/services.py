from __future__ import annotations
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from sqlmodel import select
from datetime import date
from uuid import UUID

from backend.core.DatabaseService.base import DatabaseService
from backend.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    persist_refresh_session, validate_refresh_token, rotate_refresh_session
)
from backend.core.config import get_settings
from backend.core.LoggingService import logger
from backend.domain.user.user_repo import UserRepository, RefreshSessionRepository, MFARepository
from backend.domain.organization.org_repo import PositionRepository, OrgUnitRepository, PositionClosureRepository, AssignmentRepository
from backend.domain.organization.models import Position
from backend.domain.user.models import User
from backend.domain.organization.models import Assignment

settings = get_settings()

@dataclass
class UserStaffDTO:
    id: UUID
    full_name: str
    position: str | None

class UserService:
    def __init__(self, db: DatabaseService | None = None):
        self.db = db or DatabaseService()
        self.users = UserRepository(self.db)
        self.sessions = RefreshSessionRepository(self.db)
        self.mfa = MFARepository(self.db)
        self.pos_repo = PositionRepository(self.db)
        self.unit_repo = OrgUnitRepository(self.db)
        self.closure_repo = PositionClosureRepository(self.db)
        self.assign_repo = AssignmentRepository(self.db)

    # -------- Admin-side creation --------
    async def create_user(
        self,
        username: str,
        email: Optional[str],
        password: str,
        *,
        full_name: Optional[str] = None,
        passport: Optional[str] = None,
        turniket_id: Optional[str] = None,
        is_active: bool = True,
        is_superadmin: bool = False,
    ) -> User:
        """
        Superadmin tomonidan yangi foydalanuvchi yaratish.
        - Unikal username/email tekshiriladi.
        - Parol xavfsiz xeshlanadi.
        - Role biriktirish yo‘qolgan (endi faqat assignment orqali pozitsiya orqali ishlaydi).
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError("Password too short")

        async with self.db.session_scope() as s:
            if await self.users.get_by_username(username):
                raise ValueError(f"Username '{username}' already exists")
            if email and await self.users.get_by_email(email):
                raise ValueError(f"Email '{email}' already exists")

            user = User(
                username=username,
                email=email,
                full_name=full_name,
                passport=passport,
                turniked_id=turniket_id,
                hashed_password=get_password_hash(password),
                is_active=is_active,
                is_superadmin=is_superadmin,
            )

            s.add(user)
            await s.flush()
            await s.refresh(user)
            await s.commit()

            logger.info("👤 User created via admin: {}", username)
            return user

    async def get_by_user_turniked_id(self, user_id: UUID) -> Optional[User]:
        return await self.users.get_by_user_turniked_id(user_id)

    # -------- Registration --------
    async def register_user(self, username: str, email: str, password: str, *, is_superadmin: bool = False) -> User:
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError("Password too short")

        if await self.users.get_by_username(username):
            raise ValueError("Username already exists")
        if email and await self.users.get_by_email(email):
            raise ValueError("Email already exists")

        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_superadmin=is_superadmin
        )
        created = await self.users.create(user)
        logger.info("User registered: {}", username)
        return created

    # -------- Authentication --------
    async def authenticate(self, username: str, password: str, *, ip: Optional[str] = None) -> Optional[User]:
        user = await self.users.get_by_username(username)
        if not user or not user.is_active or user.is_blocked:
            return None

        # Lockout check
        if user.locked_until and user.locked_until > settings_now():
            return None

        if not user.hashed_password or not verify_password(password, user.hashed_password):
            await self.users.register_failure(user, max_attempts=5, lock_minutes=15)
            return None

        await self.users.set_login_success(user, ip or "unknown")
        return user

    async def issue_tokens(self, user: User, *, fingerprint: Optional[str], user_agent: Optional[str],
                           ip: Optional[str]) -> Tuple[str, str]:
        # access
        from backend.core.security import AccessTokenPayload
        access = create_access_token(AccessTokenPayload(
            sub=str(user.id),
            username=user.username,
            is_superadmin=user.is_superadmin,
            roles=[],  # ⛔️ Roles o‘rniga bo‘sh ro‘yxat — endi kerak emas
        ))

        # refresh
        refresh, payload = create_refresh_token(user.id)
        await persist_refresh_session(self.db, user, refresh, payload, fingerprint, user_agent, ip)
        return access, refresh

    async def refresh_tokens(self, old_refresh: str, *, fingerprint: Optional[str], user_agent: Optional[str],
                             ip: Optional[str]) -> Tuple[str, str]:
        payload = await validate_refresh_token(self.db, old_refresh, fingerprint)
        user = await self.users.get_by_id(UUID(payload.sub))
        if not user or not user.is_active or user.is_blocked:
            raise ValueError("User not allowed")

        new_refresh, new_payload = create_refresh_token(user.id)
        await rotate_refresh_session(self.db, payload.jti, new_refresh, new_payload,
                                     fingerprint, user_agent, ip, user.id)

        from backend.core.security import AccessTokenPayload
        access = create_access_token(AccessTokenPayload(
            sub=str(user.id),
            username=user.username,
            is_superadmin=user.is_superadmin,
            roles=[],  # ⛔️ Roles bo‘sh
        ))
        return access, new_refresh

    async def revoke_all_sessions(self, user_id: UUID):
        await self.sessions.revoke_all_for_user(user_id)

    async def get_users(self):
        async with self.db.session_scope() as s:
            stmt = select(User).where(User.is_deleted == False)
            res = await s.execute(stmt)
            return res.scalars().all()

    async def get_user_position(self, position_id: UUID) -> Optional[Position]:
        return await self.pos_repo.get_by_id(position_id)

    async def get_many_by_ids(self, ids: List[UUID]) -> List[UserStaffDTO]:
        """
        Staff ro‘yxatini lavozim sarlavhasi bilan qaytaradi.
        Batch ishlaydi, N+1 yo‘q.
        """
        users = await self.users.get_many_by_ids(ids)
        if not users:
            return []

        uid_list = [u.id for u in users]
        today = date.today()

        async with self.db.session_scope() as s:
            stmt = (
                select(Assignment.user_id, Position.title)
                .join(Position, Position.id == Assignment.position_id)
                .where(
                    Assignment.user_id.in_(uid_list),
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                    Position.is_deleted == False,
                    Assignment.valid_from <= today,
                    # valid_to None yoki kelajak
                    ((Assignment.valid_to.is_(None)) | (Assignment.valid_to >= today))
                )
            )
            res = await s.execute(stmt)
            rows = res.all()

        # Har user uchun bitta asosiy sarlavha (bir nechta bo‘lsa – birinchisini olamiz)
        title_map: Dict[UUID, str] = {}
        for user_id, title in rows:
            if user_id not in title_map:
                title_map[user_id] = title

        out: List[UserStaffDTO] = []
        for u in users:
            out.append(UserStaffDTO(
                id=u.id,
                full_name=u.full_name or u.username,
                position=title_map.get(u.id)
            ))
        return out

    async def get_staff_by_unit(self, user_id: UUID, unit_id: UUID | None):
        # Barcha subordinat userlarni topamiz
        subordinate_ids = await self.assign_repo.get_users_by_subordinates(user_id)

        if not subordinate_ids:
            return []

        # Agar unit_id bo‘lsa — shu org_unit ichida filtrlaymiz
        today = date.today()

        async with self.db.session_scope() as s:
            stmt = (
                select(Assignment.user_id, Position.title, Position.org_unit_id)
                .join(Position, Position.id == Assignment.position_id)
                .where(
                    Assignment.user_id.in_(subordinate_ids),
                    Assignment.status == "ACTIVE",
                    Assignment.is_deleted == False,
                    Position.is_deleted == False,
                    Assignment.valid_from <= today,
                    ((Assignment.valid_to.is_(None)) | (Assignment.valid_to >= today))
                )
            )
            res = await s.execute(stmt)
            rows = res.all()

        title_map = {}
        unit_map = {}

        for uid, title, ouid in rows:
            if uid not in title_map:
                title_map[uid] = title
                unit_map[uid] = ouid

        # ✅ Unit filtering
        filtered = []
        for uid in subordinate_ids:
            if unit_id and unit_map.get(uid) != unit_id:
                continue  # skip if not match

            filtered.append(UserStaffDTO(
                id=uid,
                full_name=(await self.users.get_by_id(uid)).full_name,
                position=title_map.get(uid)
            ))

        return filtered

    async def build_org_tree(self, current_user_id: UUID, subordinate_ids: List[UUID]) -> dict:
        # 1️⃣ Rahbarning asosiy lavozimi
        pos_id = await self.unit_repo.get_active_position_by_user(current_user_id)
        if not pos_id:
            return {"id": current_user_id, "units": []}

        # 2️⃣ OrgUnit topamiz
        org_unit_id = await self.unit_repo.get_org_unit_by_user_id(current_user_id)
        if not org_unit_id:
            return {"id": current_user_id, "units": []}

        # 3️⃣ Root org unit
        root_unit = await self.unit_repo.get(org_unit_id)

        # 4️⃣ Position closure (rahbar nazoratidagi positionlar)
        child_positions = await self.closure_repo.get_child_positions(pos_id)
        position_ids = list(set(child_positions + [pos_id]))

        # 5️⃣ Position → staff mapping
        staff_ids = await self.assign_repo.get_users_by_positions(position_ids)
        staff_ids = [uid for uid in staff_ids if uid != current_user_id]

        staff_dtos = await self.get_many_by_ids(staff_ids)

        staff_map: Dict[UUID, List] = {pid: [] for pid in position_ids}
        for s in staff_dtos:
            # s = UserStaffDTO
            for pid in position_ids:
                staff_map[pid].append({
                    "id": s.id,
                    "full_name": s.full_name,
                    "position": s.position
                })

        # 6️⃣ Recursive unit builder
        async def build_nodes(unit):
            positions = await self.pos_repo.get_positions_by_org_unit(unit.id)

            pos_nodes = []
            for p in positions:
                pos_nodes.append({
                    "id": p.id,
                    "title": p.title,
                    "staff": staff_map.get(p.id, []),
                    "children": []
                })

            children_units = await self.unit_repo.get_children(unit.id)

            return {
                "id": unit.id,
                "name": unit.name,
                "unit_type": unit.unit_type,
                "positions": pos_nodes,
                "children": [
                    await build_nodes(child)
                    for child in children_units
                ]
            }

        tree = await build_nodes(root_unit)

        current_user = await self.users.get_by_id(current_user_id)

        return {
            "id": current_user_id,
            "full_name": current_user.full_name or current_user.username,
            "position": (await self.pos_repo.get_by_id(pos_id)).title,
            "units": [tree]
        }

def settings_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)
