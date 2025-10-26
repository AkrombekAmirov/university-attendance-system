from __future__ import annotations
from typing import Optional, Tuple, List
from uuid import UUID
from sqlmodel import select

from backend.core.DatabaseService.base import DatabaseService
from backend.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    persist_refresh_session, validate_refresh_token, rotate_refresh_session
)
from backend.core.config import get_settings
from backend.core.LoggingService import logger
from backend.domain.user.user_repo import UserRepository, RefreshSessionRepository, MFARepository
from backend.domain.organization.org_repo import PositionRepository
from backend.domain.organization.models import Position
from backend.domain.user.models import User

settings = get_settings()

class UserService:
    def __init__(self, db: DatabaseService | None = None):
        self.db = db or DatabaseService()
        self.users = UserRepository(self.db)
        self.sessions = RefreshSessionRepository(self.db)
        self.mfa = MFARepository(self.db)
        self.pos_repo = PositionRepository(self.db)

    # -------- Admin-side creation --------
    async def create_user(
        self,
        username: str,
        email: Optional[str],
        password: str,
        *,
        full_name: Optional[str] = None,
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

def settings_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)
