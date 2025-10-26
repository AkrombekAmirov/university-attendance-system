from __future__ import annotations
import time
from backend.core.middleware.request_context import get_request_context
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.LoggingService import logger
from starlette.responses import Response
from backend.domain.audit.services import AuditService
from starlette.requests import Request



class HttpAuditMiddleware(BaseHTTPMiddleware):
    """
    Mutatsion (POST, PUT, PATCH, DELETE) HTTP so‘rovlar uchun umumiy audit yozadi.
    Ushbu middleware har bir o‘zgartirish (data mutation) so‘rovini kuzatadi.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response: Response = None
        ctx = get_request_context()

        # 🔹 Mutatsion bo‘lmagan so‘rovlar uchun audit yozmaymiz
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await call_next(request)

        # 🔹 Request ma’lumotlari
        try:
            body = await request.body()
            body_preview = body.decode("utf-8")[:512] if body else None
        except Exception:
            body_preview = None

        # 🔹 AuditServis
        audit_service = AuditService()

        # 🔹 Requestni bajarish
        try:
            response = await call_next(request)
            status_code = response.status_code
            duration = (time.perf_counter() - start_time) * 1000

            await audit_service.record(
                action=f"HTTP.{request.method}",
                status="SUCCESS" if status_code < 400 else "FAIL",
                actor_user_id=ctx.get("user_id"),
                actor_ip=ctx.get("ip"),
                request_id=ctx.get("request_id"),
                http_method=request.method,
                http_path=request.url.path,
                user_agent=request.headers.get("user-agent"),
                entity_type="HTTP",
                entity_id=None,
                meta={
                    "status_code": status_code,
                    "duration_ms": round(duration, 2),
                    "body_preview": body_preview,
                },
            )

            logger.info(
                "📘 HTTP AUDIT: {method} {path} [{status}] ({duration:.2f} ms)",
                method=request.method,
                path=request.url.path,
                status=status_code,
                duration=duration,
            )

            return response

        except Exception as ex:
            # ❌ Exception holatida audit yozamiz
            duration = (time.perf_counter() - start_time) * 1000
            await audit_service.record(
                action=f"HTTP.{request.method}",
                status="FAIL",
                actor_user_id=ctx.get("user_id"),
                actor_ip=ctx.get("ip"),
                request_id=ctx.get("request_id"),
                http_method=request.method,
                http_path=request.url.path,
                user_agent=request.headers.get("user-agent"),
                entity_type="HTTP",
                entity_id=None,
                meta={
                    "error": str(ex),
                    "duration_ms": round(duration, 2),
                    "body_preview": body_preview,
                },
            )
            logger.exception(
                "❌ HTTP AUDIT FAIL: {method} {path} ({duration:.2f} ms)",
                method=request.method,
                path=request.url.path,
                duration=duration,
            )
            raise
