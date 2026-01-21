from fastapi import FastAPI, HTTPException
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
from backend.interfaces.turniked import turniked_router
from backend.core.middleware.security_headers import SecurityHeadersMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


logger = logger
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=bool(settings.DEBUG and settings.APP_ENV != "production"),
    docs_url=None if settings.APP_ENV == "production" else "/docs",
    redoc_url=None if settings.APP_ENV == "production" else "/redoc",
)
# Middlewares (order muhim)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(HttpAuditMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=getattr(settings, "ALLOWED_HOSTS", ["*"]) or ["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(
        settings,
        "CORS_ALLOW_ORIGINS",
        ["https://davomat.uznpu.uz", "https://api.davomat.uznpu.uz"],
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers

# class LoggingMiddleware(BaseHTTPMiddleware):
#     """Request/Response log middleware (for traceability)."""
#
#     async def dispatch(self, request: Request, call_next):
#         logger.info(f"➡️ {request.method} {request.url}")
#         response = await call_next(request)
#         logger.info(f"⬅️ {request.method} {request.url} - {response.status_code}")
#         return response
# app.add_middleware(LoggingMiddleware)
# @app.exception_handler(AppException)
# async def app_exception_handler(request: Request, exc: AppException):
#     logger.error(f"❌ {exc}")
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.message, "code": exc.code},
#     )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.info(f"⚠️ Validation error on {request.method} {request.url.path}")
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.info(f"⚠️ HTTPException {exc.status_code} on {request.method} {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"💥 Unexpected error on {request.method} {request.url.path}")
    content = {"detail": "Internal server error"}
    if bool(settings.DEBUG and settings.APP_ENV != "production"):
        content["error"] = str(exc)
    return JSONResponse(status_code=500, content=content)


app.include_router(user_router)
app.include_router(org_router)
app.include_router(turniked_router)


# @app.get("/health", tags=["System"])
# async def health_check():
#     return {
#         "status": "ok",
#         "db": "connected",
#         "version": app.version,
#         "env": settings.APP_ENV,
#     }