from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from fastapi import Request, HTTPException, status

from backend.core.DatabaseService.base import DatabaseService
from backend.core.LoggingService import logger
from backend.core.audit import audit_action
from backend.core.config import get_settings
from backend.core.security import validate_refresh_token
from backend.domain.user.models import User
from backend.domain.user.services import UserService
from backend.domain.organization.services import OrganizationService
from .schemas import LoginIn, RegisterIn, TokenResponse, MeOut, UserCreateIn, UserOut
from backend.interfaces.api.schemas import PositionOut


@dataclass
class UserAuthController:
    """
    Auth va foydalanuvchi boshqaruvi uchun Controller.
    - Bir request → bitta controller instance.
    - Role tizimi olib tashlangan (faqat is_superadmin flag asosida ishlaydi).
    """
    db: DatabaseService
    request: Request

    def __post_init__(self):
        self.settings = get_settings()
        self.svc = UserService(self.db)
        self.org_svc = OrganizationService(self.db)

    # ---------- helpers ----------
    def _fingerprint(self) -> Optional[str]:
        return self.request.headers.get("x-fp")

    def _user_agent(self) -> Optional[str]:
        return self.request.headers.get("user-agent")

    def _client_ip(self) -> str:
        return self.request.headers.get("x-forwarded-for") or (
            self.request.client.host if self.request.client else "unknown"
        )

    # ---------- AUTH ENDPOINTS ----------
    @audit_action(action="AUTH.LOGIN", entity_type="User")
    async def login(self, payload: LoginIn) -> TokenResponse:
        """Foydalanuvchi login."""
        user = await self.svc.authenticate(payload.username, payload.password, ip=self._client_ip())
        if not user:
            logger.warning("❌ Login failed: {}", payload.username)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or locked")

        access, refresh = await self.svc.issue_tokens(
            user,
            fingerprint=self._fingerprint(),
            user_agent=self._user_agent(),
            ip=self._client_ip(),
        )

        redirect_path = "/admin_manage" if user.is_superadmin else "/dashboard"

        logger.info("✅ Login success: {} → {}", payload.username, redirect_path)
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            redirect_path=redirect_path,
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @audit_action(action="AUTH.REFRESH", entity_type="User")
    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Tokenlarni yangilash."""
        payload = await validate_refresh_token(self.db, refresh_token, self._fingerprint())
        user_id = UUID(payload.sub)

        access, new_refresh = await self.svc.refresh_tokens(
            refresh_token,
            fingerprint=self._fingerprint(),
            user_agent=self._user_agent(),
            ip=self._client_ip(),
        )

        user = await self.svc.users.get_by_id(user_id)
        redirect_path = "/admin" if (user and user.is_superadmin) else "/dashboard"

        return TokenResponse(
            access_token=access,
            refresh_token=new_refresh,
            redirect_path=redirect_path,
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @audit_action(action="AUTH.LOGOUT_ALL", entity_type="User")
    async def logout_all(self, current: User) -> dict:
        """Foydalanuvchining barcha sessiyalarini bekor qilish."""
        await self.svc.revoke_all_sessions(current.id)
        logger.info("🔒 All sessions revoked for {}", current.username)
        return {"ok": True, "detail": "All sessions revoked"}

    # ---------- USER MANAGEMENT ----------
    @audit_action(action="AUTH.REGISTER", entity_type="User")
    async def register(self, payload: RegisterIn, actor: User) -> MeOut:
        """Yangi foydalanuvchini ro‘yxatdan o‘tkazish (faqat superadmin)."""
        if not actor.is_superadmin:
            raise HTTPException(status_code=403, detail="Only superadmin can register users")

        user = await self.svc.register_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            is_superadmin=payload.is_superadmin,
        )

        redirect_path = "/admin" if user.is_superadmin else "/dashboard"

        return MeOut(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superadmin=user.is_superadmin,
            roles=[],  # endi yo‘q, token ichida ham bo‘sh
            redirect_path=redirect_path,
        )

    async def me(self, current: User) -> MeOut:
        """Foydalanuvchi o‘z profilini olish."""
        redirect_path = "/admin" if current.is_superadmin else "/dashboard"
        return MeOut(
            id=current.id,
            username=current.username,
            email=current.email,
            full_name=current.full_name,
            is_active=current.is_active,
            is_superadmin=current.is_superadmin,
            roles=[],  # endi mavjud emas
            redirect_path=redirect_path,
        )

    @audit_action(action="USER.CREATE_SIMPLE", entity_type="User")
    async def create_user_simple(self, payload: UserCreateIn, actor: User) -> UserOut:
        """Oddiy foydalanuvchini yaratish (faqat superadmin)."""
        if not actor.is_superadmin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Only superadmin can create users.")

        user = await self.svc.create_user(
            username=payload.username,
            email=f"{payload.username}@gmail.com",
            password=payload.password,
            full_name=payload.full_name,
            is_superadmin=False,
            is_active=True,
        )

        logger.info("✅ New user created by {}: {}", actor.username, user.username)
        return user

    async def get_users(self, current: User) -> List[UserOut]:
        """Barcha foydalanuvchilarni olish."""
        return await self.svc.get_users()

    async def get_user_position_auth(self, position_id: UUID):
        """Foydalanuvchining pozitsiyasi haqida ma’lumot olish."""
        return await self.svc.get_user_position(position_id=position_id)
