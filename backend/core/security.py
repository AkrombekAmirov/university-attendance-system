from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID, uuid4
import hashlib

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from backend.core.config import get_settings
from backend.core.DatabaseService.base import DatabaseService, get_db
from backend.domain.user.user_repo import (
    UserRepository, RefreshSessionRepository
)
from backend.domain.user.models import User, RefreshSession


settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/auth/login")


# ===== Hash helpers =====
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed: str) -> bool:
    return pwd_context.verify(plain_password, hashed)

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ===== Token payloads =====
class AccessTokenPayload(BaseModel):
    sub: str
    username: str
    is_superadmin: bool = False
    roles: List[str] = Field(default_factory=list)
    iss: str = "uas.api"
    aud: str = "uas.clients"
    iat: int | None = None
    nbf: int | None = None
    exp: int | None = None
    jti: str | None = None


class RefreshTokenPayload(BaseModel):
    sub: str
    jti: str
    iss: str = "uas.api"
    aud: str = "uas.clients"
    iat: int | None = None
    nbf: int | None = None
    exp: int | None = None
    rot: bool = True  # rotated refresh


# ===== Token creators =====
def create_access_token(payload: AccessTokenPayload, minutes: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = payload.model_dump()
    to_encode.update({"iat": int(now.timestamp()), "nbf": int(now.timestamp()), "exp": int(exp.timestamp()), "jti": str(uuid4())})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: UUID, *, minutes: Optional[int] = None) -> tuple[str, RefreshTokenPayload]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=minutes or settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid4())
    payload = RefreshTokenPayload(sub=str(user_id), jti=jti, iat=int(now.timestamp()), nbf=int(now.timestamp()), exp=int(exp.timestamp()))
    token = jwt.encode(payload.model_dump(), settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, payload


# ===== Dependencies =====
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: DatabaseService = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience="uas.clients",
            issuer="uas.api"
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    async with db.session_scope() as session:
        user = await session.get(User, user_id)
        if not user or not user.is_active or user.is_blocked:
            raise HTTPException(status_code=403, detail="User is inactive or blocked")
        return user


def require_roles(required: List[str] | None = None, *, allow_superadmin: bool = True):
    required = required or []
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if allow_superadmin and user.is_superadmin:
            return user
        db = DatabaseService()
        # role codes via assignments → position → role
        from backend.domain.organization.models import Assignment, Position, Role
        from sqlmodel import select
        async with db.session_scope() as s:
            stmt = (
                select(Role.code)
                .join(Position, Position.role_id == Role.id)
                .join(Assignment, Assignment.position_id == Position.id)
                .where(Assignment.user_id == user.id, Assignment.status == "ACTIVE", Role.is_deleted == False)
            )
            res = await s.execute(stmt)
            codes = set(res.scalars().all())
        if not set(required).issubset(codes):
            raise HTTPException(status_code=403, detail=f"Required roles: {required}")
        return user
    return dependency


# ===== Refresh session utilities =====
async def persist_refresh_session(db: DatabaseService, user: User, refresh_token: str, payload: RefreshTokenPayload, fingerprint: Optional[str], user_agent: Optional[str], ip: Optional[str]):
    repo = RefreshSessionRepository(db)
    s = RefreshSession(
        user_id=user.id,
        jti=payload.jti,
        refresh_token_hash=sha256(refresh_token),
        fingerprint_hash=sha256(fingerprint) if fingerprint else None,
        user_agent=user_agent,
        ip_address=ip,
        expires_at=datetime.fromtimestamp(payload.exp, tz=timezone.utc),
    )
    await repo.create(s)

async def rotate_refresh_session(db: DatabaseService, old_jti: str, new_token: str, new_payload: RefreshTokenPayload, fingerprint: Optional[str], user_agent: Optional[str], ip: Optional[str], user_id: UUID):
    repo = RefreshSessionRepository(db)
    old = await repo.get_by_jti(old_jti)
    if not old or old.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or revoked")
    await repo.revoke(old, replaced_by_jti=new_payload.jti)
    await persist_refresh_session(db, User(id=user_id), new_token, new_payload, fingerprint, user_agent, ip)


async def validate_refresh_token(db: DatabaseService, token: str, fingerprint: Optional[str]) -> RefreshTokenPayload:
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM], audience="uas.clients", issuer="uas.api")
        payload = RefreshTokenPayload(**decoded)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    sess_repo = RefreshSessionRepository(db)
    sess = await sess_repo.get_by_jti(payload.jti)
    if not sess or sess.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Refresh session revoked")

    if datetime.now(timezone.utc) > sess.expires_at:
        raise HTTPException(status_code=401, detail="Refresh token expired")

    if fingerprint and sess.fingerprint_hash and sess.fingerprint_hash != sha256(fingerprint):
        raise HTTPException(status_code=401, detail="Device fingerprint mismatch")

    return payload
