from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import TIMESTAMP



# =====================================================
# Base Model
# =====================================================
class BaseSQLModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    is_deleted: bool = Field(default=False, nullable=False)
    version: int = Field(default=1, nullable=False)


# =====================================================
# RefreshSession Model
# =====================================================
class RefreshSession(BaseSQLModel, table=True):
    __tablename__ = "refresh_session"

    user_id: UUID = Field(foreign_key="user.id", index=True, nullable=False)
    jti: str = Field(index=True, nullable=False, unique=True, max_length=64)
    refresh_token_hash: str = Field(nullable=False, max_length=256)
    fingerprint_hash: Optional[str] = Field(default=None, max_length=256)
    user_agent: Optional[str] = Field(default=None, max_length=256)
    ip_address: Optional[str] = Field(default=None, max_length=64)
    expires_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    )
    revoked_at: Optional[datetime] = Field(default=None, index=True)
    replaced_by_jti: Optional[str] = Field(default=None, index=True)

    # user: Optional["User"] = Relationship(back_populates="sessions")

    __table_args__ = (
        Index("idx_refresh_active", "user_id", "expires_at", "revoked_at"),
        UniqueConstraint("jti", name="uq_refresh_jti"),
    )


# =====================================================
# MFASecret Model
# =====================================================
class MFASecret(BaseSQLModel, table=True):
    __tablename__ = "mfa_secret"

    user_id: UUID = Field(foreign_key="user.id", index=True, nullable=False)
    secret: str = Field(nullable=False, max_length=64)
    is_enabled: bool = Field(default=False, index=True)
    last_verified_at: Optional[datetime] = Field(default=None)

    # user: Optional["User"] = Relationship(back_populates="mfa_secret")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_mfa_user"),
    )


# =====================================================
# User Model
# =====================================================
class User(BaseSQLModel, table=True):
    __tablename__ = "user"

    username: str = Field(index=True, nullable=False, unique=True, max_length=64)
    passport: Optional[str] = Field(default=None, index=True, max_length=13)
    phone_number: Optional[str] = Field(default=None, index=True, max_length=32)
    email: Optional[str] = Field(default=None, index=True, max_length=128)
    jshshir: Optional[str] = Field(default=None, index=True, max_length=13)
    course: Optional[int] = Field(default=None, index=True)
    group: Optional[str] = Field(default=None, index=True)
    ttj_number: Optional[str] = Field(default=None, index=True)
    filial: Optional[str] = Field(default=None, index=True)

    full_name: Optional[str] = Field(default=None, index=True, max_length=128)
    language: str = Field(default="uz", max_length=8)
    timezone: str = Field(default="Asia/Tashkent", max_length=64)

    is_active: bool = Field(default=True, index=True)
    is_superadmin: bool = Field(default=False, index=True)
    is_verified: bool = Field(default=False, index=True)
    is_blocked: bool = Field(default=False, index=True)

    hashed_password: Optional[str] = Field(default=None, max_length=256)
    password_changed_at: Optional[datetime] = Field(default=None)
    auth_provider: str = Field(default="local", index=True, max_length=32)

    last_login_at: Optional[datetime] = Field(default=None)
    last_login_ip: Optional[str] = Field(default=None, max_length=64)
    failed_login_attempts: int = Field(default=0)
    last_failed_login_at: Optional[datetime] = Field(default=None)
    locked_until: Optional[datetime] = Field(default=None, index=True)

    gender: Optional[str] = Field(default=None, max_length=16)
    birth_date: Optional[datetime] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None, max_length=256)
    position_title: Optional[str] = Field(default=None, max_length=128)

    meta: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    external_ids: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    # Relationship (classik usul)
    # sessions: List["RefreshSession"] = Relationship(back_populates="user")
    # mfa_secret: Optional["MFASecret"] = Relationship(back_populates="user")

    __table_args__ = (
        UniqueConstraint("username", name="uq_user_username"),
        UniqueConstraint("email", name="uq_user_email"),
        Index("idx_user_login", "is_active", "is_blocked", "locked_until"),
    )

    def mark_login_success(self, ip: str):
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip
        self.failed_login_attempts = 0
        self.locked_until = None

    def mark_login_failure(self, max_attempts: int, lock_minutes: int):
        self.failed_login_attempts += 1
        self.last_failed_login_at = datetime.utcnow()
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lock_minutes)

    def mark_password_change(self):
        self.password_changed_at = datetime.utcnow()
