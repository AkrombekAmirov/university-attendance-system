from __future__ import annotations

import time
import uuid
import contextvars
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from jose import jwt, JWTError

from backend.core.LoggingService import logger
from backend.core.config import get_settings


# ===============================
# Context variables (thread-safe)
# ===============================
_request_id_ctx = contextvars.ContextVar("request_id", default=None)
_user_id_ctx = contextvars.ContextVar("user_id", default=None)
_ip_ctx = contextvars.ContextVar("ip_address", default=None)
_path_ctx = contextvars.ContextVar("request_path", default=None)
_method_ctx = contextvars.ContextVar("request_method", default=None)


# ===============================
# Helper functions
# ===============================
def get_request_id() -> str | None:
    return _request_id_ctx.get()


def get_user_id() -> str | None:
    return _user_id_ctx.get()


def get_ip() -> str | None:
    return _ip_ctx.get()


def get_request_context() -> dict:
    return {
        "request_id": _request_id_ctx.get(),
        "user_id": _user_id_ctx.get(),
        "ip": _ip_ctx.get(),
        "path": _path_ctx.get(),
        "method": _method_ctx.get(),
    }


# ===============================
# Middleware
# ===============================
class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Har bir FastAPI so‘rovini kuzatadi:
      - request_id (trace ID)
      - user_id (JWT dan, strict tekshiruv bilan)
      - ip manzili
      - endpoint path
      - latency
    """

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        start_time = time.perf_counter()

        # 1️⃣ Request ID
        request_id = str(uuid.uuid4())
        _request_id_ctx.set(request_id)

        # 2️⃣ Client IP
        ip = (
            request.headers.get("x-forwarded-for")
            or (request.client.host if request.client else "unknown")
        )
        _ip_ctx.set(ip)

        # 3️⃣ Path & Method
        _path_ctx.set(request.url.path)
        _method_ctx.set(request.method)

        # 4️⃣ JWT dan user_id (STRICT MODE)
        user_id = None
        auth_header = request.headers.get("authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_aud": False,
                        "verify_iss": False,
                        "require": ["exp", "sub"],
                    },
                )
                user_id = payload.get("sub") or payload.get("user_id")
            except JWTError as e:
                # Token noto‘g‘ri → user_id set qilinmaydi
                logger.bind(
                    request_id=request_id,
                    ip=ip,
                    error=str(e),
                ).warning("⚠️ Invalid JWT detected")

        _user_id_ctx.set(user_id)

        # 5️⃣ Incoming request log
        logger.bind(
            request_id=request_id,
            user_id=user_id,
            ip=ip,
            method=request.method,
            path=request.url.path,
        ).info("📨 Incoming request")

        # 6️⃣ Request processing
        try:
            response: Response = await call_next(request)
        except Exception as e:
            logger.bind(
                request_id=request_id,
                user_id=user_id,
                ip=ip,
                path=request.url.path,
                error=str(e),
            ).exception("❌ Request failed")
            raise

        # 7️⃣ Latency + response headers
        duration = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration:.2f}ms"

        logger.bind(
            request_id=request_id,
            user_id=user_id,
            ip=ip,
            status=response.status_code,
            latency=f"{duration:.2f}ms",
        ).info("✅ Request completed")

        return response
