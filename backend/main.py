from fastapi import FastAPI
from backend.core.middleware.request_context import RequestContextMiddleware
from backend.core.middleware.audit_trail import HttpAuditMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.middleware.rate_limit import RateLimitMiddleware
from backend.interfaces.users_api import user_router
from fastapi.middleware.cors import CORSMiddleware
from backend.core.LoggingService import logger
from fastapi.responses import JSONResponse
from starlette.requests import Request
from backend.core.config import get_settings
from backend.interfaces.api import org_router


logger = logger
settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Middlewares (order muhim)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(HttpAuditMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=10, window_seconds=30)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://yourdomain.uz"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers

class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/Response log middleware (for traceability)."""

    async def dispatch(self, request: Request, call_next):
        logger.info(f"➡️ {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"⬅️ {request.method} {request.url} - {response.status_code}")
        return response
# app.add_middleware(LoggingMiddleware)
# @app.exception_handler(AppException)
# async def app_exception_handler(request: Request, exc: AppException):
#     logger.error(f"❌ {exc}")
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.message, "code": exc.code},
#     )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"💥 Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


app.include_router(user_router)
app.include_router(org_router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "db": "connected",
        "version": app.version,
        "env": settings.APP_ENV,
    }
