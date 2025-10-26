# ==========================================
# models.py - Izohlar bilan tushuntirilgan
# Muallif: ChatGPT, sizning so'rovingiz asosida
# ==========================================

from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from uuid import uuid4, UUID

from sqlalchemy import UniqueConstraint, Index, text
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


# ========== Bazaviy model ==========
class BaseSQLModel(SQLModel):
    """Har bir jadval uchun umumiy audit maydonlar."""
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    is_deleted: bool = Field(default=False, nullable=False)
    version: int = Field(default=1, nullable=False)


# ========== 1) Tashkilotlar ==========
class Organization(BaseSQLModel, table=True):
    __tablename__ = "organization"

    name: str = Field(index=True, nullable=False)
    code: Optional[str] = Field(default=None, index=True)
    description: Optional[str] = None


# ========== 2) Bo‘linmalar ==========
class OrgUnit(BaseSQLModel, table=True):
    __tablename__ = "org_unit"

    organization_id: UUID = Field(foreign_key="organization.id", index=True, nullable=False)
    name: str = Field(index=True, nullable=False)
    unit_type: str = Field(index=True, nullable=False)
    parent_id: Optional[UUID] = Field(default=None, foreign_key="org_unit.id", index=True)

    path: Optional[str] = Field(default=None, index=True)
    order_no: Optional[int] = Field(default=0)
    is_active: bool = Field(default=True, nullable=False)
    extra: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    __table_args__ = (
        UniqueConstraint("organization_id", "name", "parent_id", name="uq_unit_name_per_parent"),
        Index("idx_orgunit_type_path", "unit_type", "path"),
    )


# ========== 3) Position (Lavozim) ==========
class Position(BaseSQLModel, table=True):
    __tablename__ = "position"

    org_unit_id: UUID = Field(foreign_key="org_unit.id", index=True, nullable=False)
    # role_id olib tashlandi

    title: str = Field(index=True, nullable=False)
    is_unique: bool = Field(default=True, nullable=False)
    quota: Optional[int] = Field(default=1)
    order_no: Optional[int] = Field(default=0)
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    __table_args__ = (
        UniqueConstraint("org_unit_id", "title", name="uq_position_title_per_unit"),
        Index("idx_position_unit_title", "org_unit_id", "title"),
    )


# ========== 4) Assignment (Foydalanuvchini lavozimga biriktirish) ==========
class Assignment(BaseSQLModel, table=True):
    __tablename__ = "assignment"

    position_id: UUID = Field(foreign_key="position.id", index=True, nullable=False)
    user_id: UUID = Field(foreign_key="user.id", index=True, nullable=False)
    status: str = Field(default="ACTIVE", index=True)
    valid_from: date = Field(default_factory=lambda: date.today(), nullable=False)
    valid_to: Optional[date] = Field(default=None)

    __table_args__ = (
        Index(
            "uq_active_assignment_per_position",
            "position_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'")
        ),
        Index("idx_assignment_user_status", "user_id", "status"),
    )


# ========== 5) ReportingLink (Lavozimlararo bog‘liqlik) ==========
class ReportingLink(BaseSQLModel, table=True):
    __tablename__ = "reporting_link"

    parent_position_id: UUID = Field(foreign_key="position.id", index=True, nullable=False)
    child_position_id: UUID = Field(foreign_key="position.id", index=True, nullable=False)
    relation_type: str = Field(default="LINE", nullable=False, index=True)
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    __table_args__ = (
        UniqueConstraint("parent_position_id", "child_position_id", name="uq_reporting_edge"),
        Index("idx_reporting_parent_child", "parent_position_id", "child_position_id"),
    )


# ========== 6) PositionClosure (Lavozimlar ierarxiyasi) ==========
class PositionClosure(BaseSQLModel, table=True):
    __tablename__ = "position_closure"

    parent_position_id: UUID = Field(foreign_key="position.id", index=True, nullable=False)
    child_position_id: UUID = Field(foreign_key="position.id", index=True, nullable=False)
    depth: int = Field(default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("parent_position_id", "child_position_id", name="uq_position_closure"),
        Index("idx_closure_parent_depth", "parent_position_id", "depth"),
        Index("idx_closure_child", "child_position_id"),
    )


# ========== 7) Permission (Ruxsatlar) ==========
class Permission(BaseSQLModel, table=True):
    __tablename__ = "permission"

    code: str = Field(index=True, unique=True, nullable=False)
    name: Optional[str] = None
    description: Optional[str] = None
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSONB))