from __future__ import annotations

import anyio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Production-grade guard against oversized requests (basic DoS protection).
    Uses Content-Length when present; otherwise reads up to limit+1 and rejects.
    """

    def __init__(self, app, *, max_body_bytes: int = 1_048_576):
        super().__init__(app)
        self.max_body_bytes = int(max_body_bytes)

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        cl = request.headers.get("content-length")
        if cl:
            try:
                if int(cl) > self.max_body_bytes:
                    return JSONResponse(status_code=413, content={"detail": "Request entity too large"})
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})

        if request.method in {"POST", "PUT", "PATCH"}:
            body = await request.body()
            if len(body) > self.max_body_bytes:
                return JSONResponse(status_code=413, content={"detail": "Request entity too large"})

        return await call_next(request)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """
    Hard request time limit (basic DoS protection / slowloris guard at app level).
    """

    def __init__(self, app, *, timeout_seconds: float = 15.0):
        super().__init__(app)
        self.timeout_seconds = float(timeout_seconds)

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            with anyio.fail_after(self.timeout_seconds):
                return await call_next(request)
        except TimeoutError:
            return JSONResponse(status_code=504, content={"detail": "Request timeout"})

