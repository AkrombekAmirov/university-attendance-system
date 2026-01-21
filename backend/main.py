# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from backend.core.config import get_settings
from backend.core.LoggingService import logger

from backend.core.middleware.security_headers import SecurityHeadersMiddleware
from backend.core.middleware.request_context import RequestContextMiddleware
from backend.core.middleware.request_limits import (
    RequestSizeLimitMiddleware,
    RequestTimeoutMiddleware,
)
from backend.core.middleware.rate_limit import RateLimitMiddleware
from backend.core.middleware.audit_trail import HttpAuditMiddleware

from backend.interfaces.users_api import user_router
from backend.interfaces.api import org_router
from backend.interfaces.turniked import turniked_router


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=bool(settings.DEBUG and settings.APP_ENV != "production"),
    docs_url=None if settings.APP_ENV == "production" else "/docs",
    redoc_url=None if settings.APP_ENV == "production" else "/redoc",
)
# class PreflightBypassMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         if request.method == "OPTIONS":
#             return JSONResponse(status_code=204)
#         return await call_next(request)
#
# app.add_middleware(PreflightBypassMiddleware)
# =========================================================
# 🔐 1. CORS — DOIM ENG BIRINCHI!
# =========================================================
# ⚠️ Sabab: OPTIONS preflight hech qachon bloklanmasligi shart
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS
    or [
        "https://davomat.uznpu.uz",
        "https://api.davomat.uznpu.uz",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "Accept",
        "Origin",
    ],
    max_age=600,
)

# =========================================================
# 🛡 2. Security Headers
# =========================================================
app.add_middleware(SecurityHeadersMiddleware)

# =========================================================
# 🌍 3. Trusted Hosts (DNS rebinding protection)
# =========================================================
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS or ["davomat.uznpu.uz", "api.davomat.uznpu.uz"],
)

# =========================================================
# 🧠 4. Request Context (JWT parsing, trace-id)
# =========================================================
app.add_middleware(RequestContextMiddleware)

# =========================================================
# 🧾 5. Audit Trail (AUTH / DATA EVENTS)
# =========================================================
app.add_middleware(HttpAuditMiddleware)

# =========================================================
# ⏱ 6. Request Size & Timeout (DoS / Slowloris)
# =========================================================
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_body_bytes=settings.MAX_BODY_BYTES,
)
app.add_middleware(
    RequestTimeoutMiddleware,
    timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS,
)

# =========================================================
# 🚦 7. Rate Limiting (OPTIONS exempt bo‘lishi shart)
# =========================================================
app.add_middleware(RateLimitMiddleware)

# =========================================================
# 📜 8. Minimal Logging (NO SECRETS)
# =========================================================
class SafeLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(
            "➡️ request",
            extra={
                "method": request.method,
                "path": request.url.path,
            },
        )
        response = await call_next(request)
        logger.info(
            "⬅️ response",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
            },
        )
        return response


app.add_middleware(SafeLoggingMiddleware)

# =========================================================
# 10️⃣ EXCEPTION HANDLING — NO INFORMATION LEAKAGE
# =========================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error", extra={"path": request.url.path})
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request payload"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP exception",
        extra={"path": request.url.path, "status": exc.status_code},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# =========================================================
# 🔌 Routers
# =========================================================
app.include_router(user_router)
app.include_router(org_router)
app.include_router(turniked_router)
