from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from fastapi import Form
from pydantic import BaseModel, Field, EmailStr


# ----------------------------
# Request DTOs
# ----------------------------
class LoginIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: Optional[EmailStr] = None
    password: str = Field(min_length=8, max_length=128)
    is_superadmin: bool = False


# ----------------------------
# Response DTOs
# ----------------------------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    redirect_path: str
    expires_in: int  # seconds


class MeOut(BaseModel):
    id: UUID
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_superadmin: bool
    roles: List[str] = []
    redirect_path: str


class RoleOut(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None


class UserCreateIn(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None

    @classmethod
    def as_form(
            cls,
            username: str = Form(...),
            password: str = Form(...),
            full_name: Optional[str] = Form(None),
    ):
        """FormData orqali kelgan qiymatlarni Pydantic modelga o‘tkazadi."""
        return cls(username=username, password=password, full_name=full_name)


class UserOut(BaseModel):
    id: UUID
    username: str
    full_name: Optional[str]
    is_active: bool
    # roles: Optional[List[str]]
    class Config:
        from_attributes = True


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


class RoleRead(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    rank: int
    category: Optional[str]

    class Config:
        orm_mode = True


class OrganizationCreateIn(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def as_form(
            cls,
            name: str = Form(...),
            code: Optional[str] = Form(None),
            description: Optional[str] = Form(None),
    ) -> "OrganizationCreateIn":
        return cls(name=name, code=code, description=description)
