from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB


class BaseSQLModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    is_deleted: bool = Field(default=False, nullable=False)
    version: int = Field(default=1, nullable=False)


class AuditLog(BaseSQLModel, table=True):
    """
    Audit Trail yozuvi:
      — actor_* : kim bajardi
      — request_* : HTTP darajadagi kontekst
      — action   : biznes voqeasi nomi (e.g. ORG.UNIT.CREATE)
      — entity_* : qaysi resursga nisbatan
      — status   : SUCCESS | FAIL
      — meta     : ixtiyoriy qo'shimcha ma'lumot (JSONB)
    """
    __tablename__ = "audit_log"

    # Actor
    actor_user_id: Optional[UUID] = Field(default=None, index=True)
    actor_username: Optional[str] = Field(default=None, index=True, max_length=128)
    actor_ip: Optional[str] = Field(default=None, max_length=64)

    # Request context
    request_id: Optional[str] = Field(default=None, index=True, max_length=64)
    http_method: Optional[str] = Field(default=None, max_length=12)
    http_path: Optional[str] = Field(default=None, max_length=512)
    user_agent: Optional[str] = Field(default=None, max_length=256)

    # Business
    action: str = Field(index=True, max_length=128)        # e.g. ORG.UNIT.CREATE, USER.LOGIN, HTTP.POST
    entity_type: Optional[str] = Field(default=None, index=True, max_length=64)  # e.g. OrgUnit, User, Role
    entity_id: Optional[str] = Field(default=None, index=True, max_length=64)
    status: str = Field(default="SUCCESS", index=True, max_length=16)  # SUCCESS|FAIL

    # Extra
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    __table_args__ = (
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_actor_time", "actor_user_id", "created_at"),
        Index("idx_audit_action_time", "action", "created_at"),
        Index("idx_audit_entity_time", "entity_type", "entity_id", "created_at"),
        Index("idx_audit_status", "status"),
    )
