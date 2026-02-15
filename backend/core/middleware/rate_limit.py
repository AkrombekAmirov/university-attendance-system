from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from redis.asyncio import Redis
from backend.core.middleware.ip import get_client_ip
from backend.core.config import get_settings

settings = get_settings()

PROFILE = {
    "LOGIN": (5, 300),
    "ME": (120, 60),
    "REFRESH": (20, 300),
    "AUTH": (40, 60),
    "DEFAULT": (300, 60),
}

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis: Redis | None = None

    async def dispatch(self, request: Request, call_next):
        if self.redis is None:
            self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

        ip = get_client_ip(request)
        path = request.url.path

        if path == "/users/auth/login":
            limit, window = PROFILE["LOGIN"]
        elif path == "/users/auth/me":
            limit, window = PROFILE["ME"]
        elif path == "/users/auth/refresh":
            limit, window = PROFILE["REFRESH"]
        elif path.startswith("/users/auth"):
            limit, window = PROFILE["AUTH"]
        else:
            limit, window = PROFILE["DEFAULT"]

        key = f"rl:{ip}:{path}"

        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, window)
            if count > limit:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        except Exception:
            # Redis o‘lsa → API ishlaydi
            pass

        return await call_next(request)
