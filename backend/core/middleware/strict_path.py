from __future__ import annotations

import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from backend.core.LoggingService import logger


class StrictPathAllowlistMiddleware(BaseHTTPMiddleware):
    """
    🔒 FINAL PRODUCTION STRICT PATH ALLOWLIST

    Prinsip:
    - Faqat aniq ruxsat etilgan endpointlar ishlaydi
    - Qolgan HAMMASI jim yopiladi (404)
    - Framework fingerprint yo‘qoladi
    - Recon / scan endpointlari HECH QACHON routerga yetib bormaydi
    """

    # --------------------------------------------------
    # 1️⃣ RUXSAT ETILGAN PREFIX'LAR (HIGH TRUST)
    # --------------------------------------------------
    ALLOWED_PREFIXES = (
        "/auth",
        "/organization",
        "/staff",
        "/turniked",
        "/users",
        "/health",
        "/favicon.ico",
    )

    # --------------------------------------------------
    # 2️⃣ ANIQ RUXSAT ETILGAN YAKUNIY YO‘LLAR
    # (favicon, robots, root)
    # --------------------------------------------------
    ALLOWED_EXACT = {
        "/",
        "/robots.txt",
    }

    # --------------------------------------------------
    # 3️⃣ STATIC / ASSET YO‘LLAR (agar kerak bo‘lsa)
    # --------------------------------------------------
    STATIC_REGEX = re.compile(
        r"^/(favicon\.ico|assets/|static/)",
        re.IGNORECASE,
    )

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # --------------------------------------------------
        # OPTIONS → CORS preflight → ALWAYS PASS
        # --------------------------------------------------
        if request.method == "OPTIONS":
            return await call_next(request)

        # --------------------------------------------------
        # Exact allowlist
        # --------------------------------------------------
        if path in self.ALLOWED_EXACT:
            return await call_next(request)

        # --------------------------------------------------
        # Static assets
        # --------------------------------------------------
        if self.STATIC_REGEX.match(path):
            return await call_next(request)

        # --------------------------------------------------
        # Prefix allowlist
        # --------------------------------------------------
        for prefix in self.ALLOWED_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # --------------------------------------------------
        # ❌ HAMMASINI JIM YOPAMIZ (NO SIGNAL)
        # --------------------------------------------------
        logger.warning(
            "🚫 Path blocked by strict allowlist",
            extra={
                "path": path,
                "method": request.method,
                "ip": request.client.host if request.client else "unknown",
            },
        )

        return PlainTextResponse("Not Found", status_code=404)
