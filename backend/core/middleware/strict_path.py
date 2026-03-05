from __future__ import annotations
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from backend.core.LoggingService import logger
from backend.core.config import get_settings

settings = get_settings()


class StrictPathAllowlistMiddleware(BaseHTTPMiddleware):
    """
    🔒 FINAL PRODUCTION STRICT PATH ALLOWLIST
    """

    ALLOWED_PREFIXES = (
        "/auth",
        "/organization",
        "/staff",
        "/turniked",
        "/users",
        "/hr",
        "/health",
        "/favicon.ico",
        "/api",  # Agar frontend api deb murojaat qilsa
    )

    ALLOWED_EXACT = {
        "/",
        "/robots.txt",
    }

    STATIC_REGEX = re.compile(
        r"^/(favicon\.ico|assets/|static/)",
        re.IGNORECASE,
    )

    # 🟢 YANGI: Log ifloslanishining oldini olish uchun "Jim yopiladigan" yo'llar
    SILENT_DROP_REGEX = re.compile(
        r"^/(ip|\.env|\.git|wp-admin|wp-login\.php|xmlrpc\.php|config|phpmyadmin)",
        re.IGNORECASE,
    )

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        # 🟢 YANGI: Shovqinli (skaner) botlarni logga yozmasdan, 1 millisekundda uzish
        if self.SILENT_DROP_REGEX.match(path):
            return PlainTextResponse("Not Found", status_code=404)

        # 🟢 YANGI: Development muhitida /docs va /openapi.json ishlashi uchun istisno
        if settings.APP_ENV != "production" and (
                path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc")):
            return await call_next(request)

        if path in self.ALLOWED_EXACT:
            return await call_next(request)

        if self.STATIC_REGEX.match(path):
            return await call_next(request)

        for prefix in self.ALLOWED_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Qolgan barcha shubhali ulanishlarni logga yozib yopamiz
        logger.warning(
            "🚫 Path blocked by strict allowlist",
            extra={
                "path": path,
                "method": request.method,
                "ip": request.client.host if request.client else "unknown",
            },
        )
        return PlainTextResponse("Not Found", status_code=404)