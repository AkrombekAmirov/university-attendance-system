from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from backend.core.LoggingService import logger


class HeaderSanityMiddleware(BaseHTTPMiddleware):
    """
    🔍 Header abuse & smuggling protection
    """

    MAX_HEADERS = 40

    async def dispatch(self, request: Request, call_next):
        headers = request.headers

        if len(headers) > self.MAX_HEADERS:
            logger.warning(
                "🚨 Too many headers",
                extra={
                    "count": len(headers),
                    "path": request.url.path,
                    "ip": request.client.host if request.client else "unknown",
                },
            )
            return PlainTextResponse("Not Found", status_code=404)

        return await call_next(request)
