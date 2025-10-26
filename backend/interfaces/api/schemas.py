from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date
from fastapi import Form
from uuid import UUID


# ======================================================
# ORGANIZATION
# ======================================================
class OrganizationCreateIn(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

    @classmethod
    def as_form(
            cls,
            name: str = Form(...),
            code: str = Form(...),
            description: Optional[str] = Form(None),
    ):
        return cls(name=name, code=code, description=description)


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    code: Optional[str]

    class Config:
        from_attributes = True


# ======================================================
# ROLE
# ======================================================
class RoleCreateIn(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    rank: Optional[int] = 5
    category: Optional[str] = None

    @classmethod
    def as_form(
            cls,
            code: str = Form(...),
            name: str = Form(...),
            description: Optional[str] = Form(None),
            rank: Optional[int] = Form(5),
            category: Optional[str] = Form(None),
    ):
        return cls(code=code, name=name, description=description, rank=rank, category=category)


class RoleOut(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    rank: int
    category: Optional[str]

    class Config:
        from_attributes = True


# ======================================================
# ORG UNIT
# ======================================================
class OrgUnitCreateIn(BaseModel):
    organization_id: UUID
    name: str
    unit_type: str
    parent_id: Optional[UUID] = None

    @classmethod
    def as_form(
            cls,
            organization_id: UUID = Form(...),
            name: str = Form(...),
            unit_type: str = Form(...),
            parent_id: Optional[UUID] = Form(None),
    ):
        return cls(organization_id=organization_id, name=name, unit_type=unit_type, parent_id=parent_id)


class OrgUnitOut(BaseModel):
    id: UUID
    name: str
    unit_type: str
    parent_id: Optional[UUID]
    is_active: bool

    class Config:
        from_attributes = True


# ======================================================
# POSITION
# ======================================================

class PositionCreateIn(BaseModel):
    org_unit_id: UUID
    title: str
    is_unique: bool = True
    quota: Optional[int] = None
    parent_position_id: Optional[UUID] = None  # 🔥 Yangi qo‘shildi

    @classmethod
    def as_form(
            cls,
            org_unit_id: str = Form(...),
            title: str = Form(...),
            is_unique: bool = Form(True),
            quota: Optional[int] = Form(None),
            parent_position_id: Optional[str] = Form(None),  # 🔥
    ):
        return cls(
            org_unit_id=UUID(org_unit_id),
            title=title,
            is_unique=is_unique,
            quota=quota,
            parent_position_id=UUID(parent_position_id) if parent_position_id else None
        )


class PositionOut(BaseModel):
    id: UUID
    org_unit_id: UUID
    title: str
    is_unique: bool
    quota: Optional[int]

    class Config:
        from_attributes = True


# ========================
# Assignment Schemas
# ========================

class AssignmentCreateIn(BaseModel):
    position_id: UUID
    user_id: UUID
    status: Optional[str] = "ACTIVE"
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    rank: Optional[str] = None
    category: Optional[str] = None

    @classmethod
    def as_form(
            cls,
            position_id: UUID = Form(...),
            user_id: UUID = Form(...),
            status: Optional[str] = Form("ACTIVE"),
            valid_from: Optional[date] = Form(None),
            valid_to: Optional[date] = Form(None),
            rank: Optional[str] = Form(None),
            category: Optional[str] = Form(None),
    ):
        return cls(
            position_id=position_id,
            user_id=user_id,
            status=status,
            valid_from=valid_from,
            valid_to=valid_to,
            rank=rank,
            category=category,
        )


class AssignmentOut(BaseModel):
    id: UUID
    position_id: UUID
    user_id: UUID
    status: str
    valid_from: date
    valid_to: Optional[date]

    class Config:
        from_attributes = True


class ReportingLinkCreateIn(BaseModel):
    parent_position_id: UUID
    child_position_id: UUID
    relation_type: Optional[str] = "LINE"
    meta: Optional[dict] = None

    @classmethod
    def as_form(
            cls,
            parent_position_id: UUID = Form(...),
            child_position_id: UUID = Form(...),
            relation_type: Optional[str] = Form("LINE"),
            meta: Optional[dict] = Form(None),
    ):
        return cls(
            parent_position_id=parent_position_id,
            child_position_id=child_position_id,
            relation_type=relation_type,
            meta=meta,
        )


class ReportingLinkOut(BaseModel):
    id: UUID
    parent_position_id: UUID
    child_position_id: UUID
    relation_type: str
    meta: Optional[dict]

    class Config:
        from_attributes = True


class PositionClosureOut(BaseModel):
    id: UUID
    parent_position_id: UUID
    child_position_id: UUID
    depth: int

    class Config:
        from_attributes = True


class PositionClosureCreateIn(BaseModel):
    parent_position_id: UUID
    child_position_id: UUID
    depth: int

    @classmethod
    def as_form(
            cls,
            parent_position_id: UUID = Form(...),
            child_position_id: UUID = Form(...),
            depth: int = Form(...),
    ):
        return cls(
            parent_position_id=parent_position_id,
            child_position_id=child_position_id,
            depth=depth,
        )
