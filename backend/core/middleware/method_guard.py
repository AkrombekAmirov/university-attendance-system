from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from backend.core.LoggingService import logger


class HttpMethodGuardMiddleware(BaseHTTPMiddleware):
    """
    🔒 Blocks unused / dangerous HTTP methods
    """

    ALLOWED_METHODS = {"GET", "POST", "OPTIONS"}

    async def dispatch(self, request: Request, call_next):
        if request.method not in self.ALLOWED_METHODS:
            logger.warning(
                "🚫 HTTP method blocked",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "ip": request.client.host if request.client else "unknown",
                },
            )
            return PlainTextResponse("Not Found", status_code=404)

        return await call_next(request)
