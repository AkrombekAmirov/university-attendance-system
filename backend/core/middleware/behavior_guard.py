import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from backend.core.LoggingService import logger


class BehaviorGuardMiddleware(BaseHTTPMiddleware):
    """
    🧠 Simple behavior fingerprinting (in-memory)
    """

    WINDOW = 10  # seconds
    MAX_REQUESTS = 30

    _store = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        now = time.time()

        self._store[ip] = [t for t in self._store[ip] if now - t < self.WINDOW]
        self._store[ip].append(now)

        if len(self._store[ip]) > self.MAX_REQUESTS:
            logger.warning(
                "🤖 Bot-like behavior blocked",
                extra={
                    "ip": ip,
                    "count": len(self._store[ip]),
                    "path": request.url.path,
                },
            )
            return PlainTextResponse("Not Found", status_code=404)

        return await call_next(request)
