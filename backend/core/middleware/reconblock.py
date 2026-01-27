# backend/core/middleware/recon_block.py

import re
from urllib.parse import unquote

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.core.LoggingService import logger


class ReconBlockMiddleware(BaseHTTPMiddleware):
    """
    Bloklaydi:
    - Skaner User-Agent’larni (nmap, burp, etc.)
    - Xavfli yo‘llarni (.git, .env, backup, admin, swagger, etc.)
    - Path traversal harakatlarini
    - SQLi / XSS pattern’larini URL path/query’da
    """

    # 1. Skaner User-Agent kalit so'zlari (case-insensitive — re.IGNORECASE bilan)
    SUSPICIOUS_UA_KEYWORDS = [
        "nmap",
        "burp",
        "sqlmap",
        "nikto",
        "dirbuster",
        "acunetix",
        "nessus",
        "metasploit",
        "curl.*malicious",
        "python-requests.*scanner",
    ]

    # 2. Xavfli yo‘llar (pastki registerda saqlanadi)
    SUSPICIOUS_PATHS = {
        "/.git",
        "/.env",
        "/.well-known",
        "/backup",
        "/backups",
        "/db_backup",
        "/adminer",
        "/phpmyadmin",
        "/swagger",
        "/swagger.json",
        "/openapi.json",
        "/redoc",
        "/docs",
        "/graphql",
        "/actuator",
        "/wp-admin",
        "/manager",
        "/webdav",
        "/test",
        "/tests",
        "/tmp",
        "/logs",
        "/log",
        "/config",
        "/settings",
        "/vendor",
        "/node_modules",
        "/docker-compose.yml",
        "/dockerfile",
        "/readme.md",
        "/license",
        "/changelog",
        "/composer.json",
        "/package.json",
        "/.htaccess",
        "/.bash_history",
        "/.ssh",
        "/passwd",
        "/shadow",
    }

    # 3. Xavfli pattern’lar (traversal, SQLi, XSS) — case-insensitive
    DANGEROUS_PATTERNS = [
        r"\.\./",           # Directory traversal
        r"union\s+select",  # SQLi
        r"\<script\>",      # Basic XSS
        r"javascript:",     # JS protocol
        r"vbscript:",       # VBScript
        r"onload\s*=",      # Event-based XSS
        r"eval\s*\(",       # Code eval
    ]

    def __init__(self, app):
        super().__init__(app)
        # ✅ TO'G'RI: Bitta regex + re.IGNORECASE
        ua_pattern = "|".join(self.SUSPICIOUS_UA_KEYWORDS)
        self.ua_regex = re.compile(ua_pattern, re.IGNORECASE)

        danger_pattern = "|".join(self.DANGEROUS_PATTERNS)
        self.danger_regex = re.compile(danger_pattern, re.IGNORECASE)

    async def dispatch(self, request: Request, call_next):
        # OPTIONS so'rovlarini o'tkazib yuborish (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # 1. User-Agent tekshiruvi
        user_agent = request.headers.get("user-agent", "")
        if user_agent and self.ua_regex.search(user_agent):
            logger.warning(
                "🚨 Blocked reconnaissance attempt by User-Agent",
                extra={
                    "ip": client_ip,
                    "ua": user_agent[:100],
                    "path": request.url.path,
                    "reason": "suspicious_user_agent",
                },
            )
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        # 2. Yo'l (path) tekshiruvi — pastki registerda
        raw_path = request.url.path.lower()
        decoded_path = unquote(raw_path).lower()

        for suspicious in self.SUSPICIOUS_PATHS:
            if raw_path.startswith(suspicious) or decoded_path.startswith(suspicious):
                logger.warning(
                    "🚨 Blocked access to sensitive path",
                    extra={
                        "ip": client_ip,
                        "path": raw_path,
                        "reason": "sensitive_path_access",
                    },
                )
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        # 3. Xavfli pattern’lar
        full_url = str(request.url).lower()
        if self.danger_regex.search(full_url):
            logger.warning(
                "🚨 Blocked payload in URL",
                extra={
                    "ip": client_ip,
                    "url": full_url[:200],
                    "reason": "malicious_pattern",
                },
            )
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        return await call_next(request)