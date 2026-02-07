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
        user = await self.svc.authenticate(
            payload.username,
            payload.password,
            ip=self._client_ip(),
        )

        if not user:
            # 🔥 Failed login ham audit + rate-limit bilan bog‘lanadi
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

        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            redirect_path=redirect_path,
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @audit_action(action="AUTH.REFRESH", entity_type="User")
    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = await validate_refresh_token(
            self.db,
            refresh_token,
            self._fingerprint(),
        )

        user_id = UUID(payload.sub)

        access, new_refresh = await self.svc.refresh_tokens(
            refresh_token,
            fingerprint=self._fingerprint(),
            user_agent=self._user_agent(),
            ip=self._client_ip(),
        )

        user = await self.svc.users.get_by_id(user_id)

        redirect_path = decide_redirect(
            is_superadmin=user.is_superadmin if user else False,
            meta=user.meta if user else None
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
        # from openpyxl import load_workbook
        # from backend.file_path import get_file_path
        # import secrets
        # import string
        # import re
        # from pathlib import Path
        #
        # # ─────────────────────────────
        # # PASSWORD GENERATOR
        # # ─────────────────────────────
        # def generate_password(length: int = 12) -> str:
        #     alphabet = (
        #             string.ascii_lowercase +
        #             string.ascii_uppercase +
        #             string.digits +
        #             "!@#$%&*"
        #     )
        #     while True:
        #         password = ''.join(secrets.choice(alphabet) for _ in range(length))
        #         if (
        #                 any(c.islower() for c in password) and
        #                 any(c.isupper() for c in password) and
        #                 any(c.isdigit() for c in password) and
        #                 any(c in "!@#$%&*" for c in password)
        #         ):
        #             return password
        #
        # # ─────────────────────────────
        # # USERNAME NORMALIZER
        # # ─────────────────────────────
        # def normalize_username(full_name: str) -> str:
        #     if not full_name:
        #         return ""
        #
        #     name = full_name.lower()
        #
        #     replace_map = {
        #         "o‘": "o", "o'": "o",
        #         "g‘": "g", "g'": "g",
        #     }
        #
        #     for k, v in replace_map.items():
        #         name = name.replace(k, v)
        #
        #     name = re.sub(r"[^a-z\s]", "", name)
        #     parts = name.split()
        #
        #     if len(parts) < 2:
        #         return ""
        #
        #     family = parts[0]
        #     first_name = parts[1]
        #     return f"{first_name}{family}"
        #
        # # ─────────────────────────────
        # # LOAD EXCEL
        # # ─────────────────────────────
        # file = await get_file_path("hr_list.xlsx")
        # workbook = load_workbook(filename=file)
        # sheet = workbook.active
        # rows = list(sheet.iter_rows(min_row=1, values_only=True))
        #
        # # ─────────────────────────────
        # # TXT FILE PREPARE
        # # ─────────────────────────────
        # output_file = Path("created_users.txt")
        #
        # with output_file.open("w", encoding="utf-8") as f:
        #     for row in rows:
        #         full_name = row[0]
        #         username = normalize_username(full_name)
        #
        #         if not username:
        #             continue
        #
        #         password = generate_password()
        #
        #         # 🔐 TXT ga yozish
        #         f.write(f"{username} : {password}\n")
        #
        #         # 👤 USER CREATE
        #         await self.svc.create_user(
        #             username=username,
        #             email=f"{username}@uznpu.com",
        #             password=password,  # ⚠️ hashing svc ichida bo‘lishi kerak
        #             full_name=full_name,
        #             passport=None,
        #             turniket_id=None,
        #             is_superadmin=False,
        #             is_active=True,
        #         )

        # ─────────────────────────────
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
