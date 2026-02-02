from __future__ import annotations

import re
from urllib.parse import unquote

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from backend.core.LoggingService import logger


class ReconBlockMiddleware(BaseHTTPMiddleware):
    """
    🔥 FINAL PRODUCTION RECON & RCE BLOCKER

    Himoya qiladi:
    - Automated scanners (UA based)
    - Sensitive path probing
    - Path traversal
    - SQLi / XSS (low-noise)
    - RCE / command injection (base64, shell, curl, wget, etc.)
    - Obfuscated payloads (URL encoded)

    Prinsiplar:
    - Allowlist'dan keyin ishlaydi
    - Jim bloklash (404)
    - Minimal false-positive
    """

    # --------------------------------------------------
    # 1️⃣ Scanner / Recon User-Agents
    # --------------------------------------------------
    UA_REGEX = re.compile(
        r"(nmap|sqlmap|nikto|acunetix|dirbuster|dirb|burp|nessus|metasploit|masscan)",
        re.IGNORECASE,
    )

    # --------------------------------------------------
    # 2️⃣ Sensitive / forbidden paths (only if reached)
    # --------------------------------------------------
    PATH_REGEX = re.compile(
        r"(^|/)(\.git|\.env|phpmyadmin|adminer|swagger|openapi|redoc|"
        r"actuator|wp-admin|wp-login|server-status|manager|webdav|"
        r"\.ssh|\.bash_history|passwd|shadow)(/|$)",
        re.IGNORECASE,
    )

    # --------------------------------------------------
    # 3️⃣ Directory traversal
    # --------------------------------------------------
    TRAVERSAL_REGEX = re.compile(r"(\.\./|\.\.\\)", re.IGNORECASE)

    # --------------------------------------------------
    # 4️⃣ SQLi / XSS (conservative, low false-positive)
    # --------------------------------------------------
    INJECTION_REGEX = re.compile(
        r"(union\s+select|select\s+.*\s+from|<script|javascript:|onload\s*=)",
        re.IGNORECASE,
    )

    # --------------------------------------------------
    # 5️⃣ RCE / Command execution (HIGH SEVERITY)
    # --------------------------------------------------
    RCE_REGEX = re.compile(
        r"(base64\s*-d|/bin/(sh|bash)|bash\s+-c|sh\s+-c|"
        r"cmd=|exec=|system\(|popen\(|"
        r"wget\s|curl\s|nc\s|netcat\s|"
        r"python\s+-c|perl\s+-e|ruby\s+-e|"
        r"powershell|certutil)",
        re.IGNORECASE,
    )

    async def dispatch(self, request: Request, call_next):
        # --------------------------------------------------
        # OPTIONS → CORS preflight → ALWAYS PASS
        # --------------------------------------------------
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")[:150]

        raw_path = request.url.path
        decoded_url = unquote(str(request.url)).lower()

        # --------------------------------------------------
        # 1️⃣ Recon User-Agent
        # --------------------------------------------------
        if user_agent and self.UA_REGEX.search(user_agent):
            logger.warning(
                "🚨 Recon UA blocked",
                extra={
                    "ip": client_ip,
                    "ua": user_agent,
                    "path": raw_path,
                    "layer": "ua",
                },
            )
            return PlainTextResponse("Not Found", status_code=404)

        # --------------------------------------------------
        # 2️⃣ Sensitive path probing
        # --------------------------------------------------
        if self.PATH_REGEX.search(raw_path):
            logger.warning(
                "🚨 Sensitive path blocked",
                extra={
                    "ip": client_ip,
                    "path": raw_path,
                    "layer": "path",
                },
            )
            return PlainTextResponse("Not Found", status_code=404)

        # --------------------------------------------------
        # 3️⃣ Path traversal
        # --------------------------------------------------
        if self.TRAVERSAL_REGEX.search(decoded_url):
            logger.warning(
                "🚨 Path traversal blocked",
                extra={
                    "ip": client_ip,
                    "url": decoded_url[:200],
                    "layer": "traversal",
                },
            )
            return PlainTextResponse("Not Found", status_code=404)

        # --------------------------------------------------
        # 4️⃣ SQLi / XSS (low noise)
        # --------------------------------------------------
        if self.INJECTION_REGEX.search(decoded_url):
            logger.warning(
                "🚨 Injection attempt blocked",
                extra={
                    "ip": client_ip,
                    "url": decoded_url[:200],
                    "layer": "injection",
                },
            )
            return PlainTextResponse("Not Found", status_code=404)

        # --------------------------------------------------
        # 5️⃣ RCE / Command execution (CRITICAL)
        # --------------------------------------------------
        if self.RCE_REGEX.search(decoded_url):
            logger.critical(
                "🔥 RCE attempt blocked",
                extra={
                    "ip": client_ip,
                    "url": decoded_url[:200],
                    "layer": "rce",
                },
            )
            return PlainTextResponse("Not Found", status_code=404)

        # --------------------------------------------------
        # PASS TO NEXT MIDDLEWARE / ROUTER
        # --------------------------------------------------
        return await call_next(request)
