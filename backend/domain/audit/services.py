from __future__ import annotations
from backend.domain.audit.models import AuditLog
from backend.core.DatabaseService.base import DatabaseService, logger
# from backend.infrastructure.persistence.audit_repo import AuditRepository
from typing import Optional, Any, Dict
from uuid import UUID
from backend.domain.audit.audit_repo import AuditRepository



class AuditService:
    """Business-level audit yozuvlarini yaratish uchun servis."""
    def __init__(self, db: DatabaseService | None = None):
        self.db = db or DatabaseService()
        self.repo = AuditRepository(self.db)

    async def record(
        self,
        *,
        action: str,
        status: str = "SUCCESS",
        actor_user_id: Optional[UUID] = None,
        actor_username: Optional[str] = None,
        actor_ip: Optional[str] = None,
        request_id: Optional[str] = None,
        http_method: Optional[str] = None,
        http_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        log = AuditLog(
            action=action,
            status=status,
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            actor_ip=actor_ip,
            request_id=request_id,
            http_method=http_method,
            http_path=http_path,
            user_agent=user_agent,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            meta=meta,
        )
        created = await self.repo.create(log)
        logger.info("🧾 Audit recorded: {action} ({status})", action=action, status=status)
        return created
