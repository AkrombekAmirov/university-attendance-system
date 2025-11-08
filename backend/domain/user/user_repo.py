from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlmodel import select
from backend.core.DatabaseService.repositories import BaseRepository
from backend.core.DatabaseService.base import DatabaseService
from backend.domain.user.models import User, RefreshSession, MFASecret


class UserRepository(BaseRepository[User]):
    def __init__(self, db: DatabaseService | None = None):
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        async with self.db.session_scope() as s:
            res = await s.execute(select(User).where(User.username == username, User.is_deleted == False))
            return res.scalar_one_or_none()

    async def get_by_user_turniked_id(self, turniked_id: UUID) -> Optional[User]:
        async with self.db.session_scope() as s:
            res = await s.execute(select(User).where(User.turniked_id == turniked_id, User.is_deleted == False))
            return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self.db.session_scope() as s:
            res = await s.execute(select(User).where(User.email == email, User.is_deleted == False))
            return res.scalar_one_or_none()

    async def set_login_success(self, user: User, ip: str):
        async with self.db.session_scope() as s:
            user.mark_login_success(ip)
            await s.merge(user)

    async def register_failure(self, user: User, max_attempts: int, lock_minutes: int):
        async with self.db.session_scope() as s:
            user.mark_login_failure(max_attempts, lock_minutes)
            await s.merge(user)


class RefreshSessionRepository(BaseRepository[RefreshSession]):
    def __init__(self, db: DatabaseService | None = None):
        super().__init__(RefreshSession, db)

    async def get_by_jti(self, jti: str) -> Optional[RefreshSession]:
        async with self.db.session_scope() as s:
            res = await s.execute(select(RefreshSession).where(RefreshSession.jti == jti))
            return res.scalar_one_or_none()

    async def revoke(self, session: RefreshSession, *, replaced_by_jti: Optional[str] = None):
        async with self.db.session_scope() as s:
            session.revoked_at = datetime.utcnow()
            session.replaced_by_jti = replaced_by_jti
            await s.merge(session)

    async def revoke_all_for_user(self, user_id: UUID):
        async with self.db.session_scope() as s:
            res = await s.execute(select(RefreshSession).where(
                RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None)
            ))
            for sess in res.scalars().all():
                sess.revoked_at = datetime.utcnow()
                await s.merge(sess)


class MFARepository(BaseRepository[MFASecret]):
    def __init__(self, db: DatabaseService | None = None):
        super().__init__(MFASecret, db)

    async def get_by_user(self, user_id: UUID) -> Optional[MFASecret]:
        async with self.db.session_scope() as s:
            res = await s.execute(select(MFASecret).where(MFASecret.user_id == user_id))
            return res.scalar_one_or_none()
