from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from starlette.requests import Request
from backend.core.config import get_settings
from redis.asyncio import Redis
import time

settings = get_settings()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    IP asosida oddiy rate limit (Redis).
    Misol: LOGIN endpoint uchun 5 req/30s va hokazo.
    """

    def __init__(self, app, max_requests: int = 5, window_seconds: int = 30):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.redis = None

    async def dispatch(self, request: Request, call_next):
        if self.redis is None:
            self.redis = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

        ip = request.headers.get("x-forwarded-for") or request.client.host or "unknown"
        key = f"rl:{ip}:{request.url.path}"
        now = int(time.time())

        # increment
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, self.window)

        if current > self.max_requests:
            return JSONResponse({"detail": "Too many requests"}, status_code=429)

        return await call_next(request)
