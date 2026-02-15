from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlmodel import select
from backend.core.DatabaseService.repositories import BaseRepository
from backend.core.DatabaseService.base import DatabaseService
from backend.domain.user.models import User, RefreshSession, MFASecret


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(User).where(
                    User.username == username,
                    User.is_deleted == False
                )
            )
            return result.scalar_one_or_none()

    async def get_by_user_turniked_id(self, turniked_id: UUID) -> Optional[User]:
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(User).where(
                    User.turniked_id == turniked_id,
                    User.is_deleted == False
                )
            )
            return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(User).where(
                    User.email == email,
                    User.is_deleted == False
                )
            )
            return result.scalar_one_or_none()

    async def set_login_success(self, user: User, ip: str):
        async with self.db.session_scope() as session:
            user.mark_login_success(ip)
            session.add(user)

    async def register_failure(self, user: User, max_attempts: int, lock_minutes: int):
        async with self.db.session_scope() as session:
            user.mark_login_failure(max_attempts, lock_minutes)
            session.add(user)

    async def get_many_by_ids(self, ids: List[UUID]) -> List[User]:
        if not ids:
            return []

        async with self.db.session_scope() as session:
            result = await session.execute(
                select(User).where(
                    User.id.in_(ids),
                    User.is_deleted == False,
                    User.is_active == True
                )
            )
            return list(result.scalars().all())


class RefreshSessionRepository(BaseRepository[RefreshSession]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(RefreshSession, db)

    async def get_by_jti(self, jti: str) -> Optional[RefreshSession]:
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(RefreshSession).where(
                    RefreshSession.jti == jti
                )
            )
            return result.scalar_one_or_none()

    async def revoke(self, session_data: RefreshSession, *, replaced_by_jti: Optional[str] = None):
        async with self.db.session_scope() as session:
            session_data.revoked_at = datetime.utcnow()
            session_data.replaced_by_jti = replaced_by_jti
            session.add(session_data)

    async def revoke_all_for_user(self, user_id: UUID):
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(RefreshSession).where(
                    RefreshSession.user_id == user_id,
                    RefreshSession.revoked_at.is_(None)
                )
            )

            sessions = result.scalars().all()
            now = datetime.utcnow()

            for sess in sessions:
                sess.revoked_at = now
                session.add(sess)


class MFARepository(BaseRepository[MFASecret]):
    def __init__(self, db: Optional[DatabaseService] = None):
        super().__init__(MFASecret, db)

    async def get_by_user(self, user_id: UUID) -> Optional[MFASecret]:
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(MFASecret).where(
                    MFASecret.user_id == user_id
                )
            )
            return result.scalar_one_or_none()