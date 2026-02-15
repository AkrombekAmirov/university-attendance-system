from __future__ import annotations

from backend.domain.audit.models import AuditLog
from backend.core.DatabaseService.repositories import BaseRepository, DatabaseService
from typing import List, Optional, Dict, Any
from sqlmodel import select, and_
from sqlalchemy import func



class AuditRepository(BaseRepository[AuditLog]):
    """Audit loglar bilan ishlash uchun minimal CRUD + query helperlar."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(AuditLog, db)

    async def recent_by_actor(self, actor_user_id, limit: int = 20) -> List[AuditLog]:
        async with self.db.session_scope() as session:
            stmt = (
                select(AuditLog)
                .where(AuditLog.actor_user_id == actor_user_id, AuditLog.is_deleted == False)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
            res = await session.execute(stmt)
            return res.scalars().all()

    async def count_actions(self, action: str) -> int:
        async with self.db.session_scope() as session:
            stmt = select(func.count()).select_from(AuditLog).where(AuditLog.action == action, AuditLog.is_deleted == False)
            res = await session.execute(stmt)
            return int(res.scalar() or 0)
