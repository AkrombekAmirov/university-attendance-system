from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from fastapi import Request, HTTPException, status, Response

from backend.core.DatabaseService.base import DatabaseService
from backend.core.LoggingService import logger
from backend.core.audit import audit_action
from backend.core.config import get_settings
from backend.core.security import validate_refresh_token, check_login_attempts, increment_login_attempts, clear_login_attempts
from backend.domain.user.models import User
from backend.domain.user.services import UserService
from backend.domain.organization.services import OrganizationService
from .schemas import LoginIn, RegisterIn, TokenResponse, MeOut, UserCreateIn, UserOut, UserUpdateIn
from backend.interfaces.users_api.policies import decide_redirect


@dataclass
class UserAuthController:
    """
    Auth va foydalanuvchi boshqaruvi uchun Controller.
    Bir request → bitta controller instance.
    """
    db: DatabaseService
    request: Request
    response: Response # Cookie uchun kerak

    def __post_init__(self):
        self.settings = get_settings()
        self.svc = UserService(self.db)
        self.org_svc = OrganizationService(self.db)

    # ---------- helpers ----------
    def _fingerprint(self) -> Optional[str]:
        return self.request.headers.get("x-fp") or "unknown"

    def _user_agent(self) -> Optional[str]:
        return self.request.headers.get("user-agent") or "unknown"

    def _client_ip(self) -> str:
        return (
                self.request.headers.get("x-forwarded-for")
                or (self.request.client.host if self.request.client else "unknown")
        )

    # ---------- AUTH ----------
    @audit_action(action="AUTH.LOGIN", entity_type="User")
    async def login(self, payload: LoginIn) -> TokenResponse:
        # 1. Rate Limit Check
        await check_login_attempts(payload.username, self._client_ip())

        user = await self.svc.authenticate(
            payload.username,
            payload.password,
            ip=self._client_ip(),
        )

        if not user:
            # 2. Increment Failed Attempts
            await increment_login_attempts(payload.username, self._client_ip())
            
            logger.warning(
                "❌ Login failed",
                extra={
                    "username": payload.username,
                    "ip": self._client_ip(),
                    "ua": self._user_agent(),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or locked",
            )

        # 3. Clear Attempts on Success
        await clear_login_attempts(payload.username, self._client_ip())

        access, refresh = await self.svc.issue_tokens(
            user,
            fingerprint=self._fingerprint(),
            user_agent=self._user_agent(),
            ip=self._client_ip(),
        )

        redirect_path = decide_redirect(
            is_superadmin=user.is_superadmin,
            meta=user.meta
        )

        logger.info(
            "✅ Login success",
            extra={
                "username": payload.username,
                "ip": self._client_ip(),
                "redirect": redirect_path,
            },
        )

        # 4. Set HttpOnly Cookies (XSS Protection)
        # Access token qisqa muddatli, refresh token uzoq muddatli
        self.response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True, # Productionda True bo'lishi shart (HTTPS)
            samesite="lax",
            max_age=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        self.response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=self.settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        )

        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            redirect_path=redirect_path,
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @audit_action(action="AUTH.REFRESH", entity_type="User")
    async def refresh(self, refresh_token: str) -> TokenResponse:
        # Cookie dan olishga harakat qilamiz, agar body da bo'lmasa
        token_to_use = refresh_token or self.request.cookies.get("refresh_token")
        
        if not token_to_use:
             raise HTTPException(status_code=401, detail="Refresh token missing")

        payload = await validate_refresh_token(
            self.db,
            token_to_use,
            self._fingerprint(),
        )

        user_id = UUID(payload.sub)

        access, new_refresh = await self.svc.refresh_tokens(
            token_to_use,
            fingerprint=self._fingerprint(),
            user_agent=self._user_agent(),
            ip=self._client_ip(),
        )

        user = await self.svc.users.get_by_id(user_id)

        redirect_path = decide_redirect(
            is_superadmin=user.is_superadmin if user else False,
            meta=user.meta if user else None
        )
        
        # Update Cookies
        self.response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        self.response.set_cookie(
            key="refresh_token",
            value=new_refresh,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=self.settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        )

        return TokenResponse(
            access_token=access,
            refresh_token=new_refresh,
            redirect_path=redirect_path,
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @audit_action(action="AUTH.LOGOUT_ALL", entity_type="User")
    async def logout_all(self, current: User) -> dict:
        await self.svc.revoke_all_sessions(current.id)
        
        # Clear Cookies
        self.response.delete_cookie("access_token")
        self.response.delete_cookie("refresh_token")
        
        logger.info(
            "🔒 All sessions revoked",
            extra={"user": current.username},
        )
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

        redirect_path = "/admin_manage/users" if user.is_superadmin else "/staff/users"

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
        redirect_path = decide_redirect(
            is_superadmin=current.is_superadmin,
            meta=current.meta,
        )

        return MeOut(
            id=current.id,
            username=current.username,
            email=current.email,
            full_name=current.full_name,
            is_active=current.is_active,
            is_superadmin=current.is_superadmin,
            roles=[],
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
            passport=payload.passport,
            turniket_id=payload.turniket_id,
            is_superadmin=False,
            is_active=True,
        )

        logger.info("✅ New user created by {}: {}", actor.username, user.username)
        return user

    async def get_users(self, current: User) -> List[UserOut]:
        return await self.svc.get_users()

    async def get_user_position_auth(self, position_id: UUID):
        """Foydalanuvchining pozitsiyasi haqida ma’lumot olish."""
        return await self.svc.get_user_position(position_id=position_id)

    async def list_full_for_users(self, current: User):
        if not current.is_superadmin:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        return await self.svc.list_full_with_assignment()

    async def update_user_basic(
            self,
            user_id: UUID,
            payload: UserUpdateIn,
            current: User
    ):
        if not current.is_superadmin:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")

        return await self.svc.update_user_basic(user_id=user_id, payload=payload)
