from __future__ import annotations

import math
from urllib.parse import parse_qs

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from backend.core.LoggingService import logger


def shannon_entropy(data: str) -> float:
    if not data or len(data) < 20:  # 👈 juda qisqa bo‘lsa tekshirmaymiz
        return 0.0
    freq = {c: data.count(c) for c in set(data)}
    length = len(data)
    return -sum((f / length) * math.log2(f / length) for f in freq.values())


class PayloadEntropyMiddleware(BaseHTTPMiddleware):
    """
    🔥 PRODUCTION-GRADE entropy detector

    Tekshiradi faqat:
    - uzun (>=20 char)
    - bitta parametrli
    - shubhali nomli parametrlarda
    """

    ENTROPY_THRESHOLD = 4.6  # 🔥 ko‘tarildi
    MAX_PARAM_LENGTH = 500

    # ❌ Tekshirilmaydigan param nomlari (ALLOWLIST)
    SAFE_PARAM_NAMES = {
        "token",
        "access_token",
        "refresh_token",
        "jwt",
        "id",
        "uuid",
        "page",
        "limit",
        "offset",
        "from",
        "to",
    }

    async def dispatch(self, request: Request, call_next):
        raw_query = request.url.query
        if not raw_query:
            return await call_next(request)

        params = parse_qs(raw_query)

        for key, values in params.items():
            if key.lower() in self.SAFE_PARAM_NAMES:
                continue

            for value in values:
                if len(value) < 20:
                    continue

                if len(value) > self.MAX_PARAM_LENGTH:
                    logger.critical(
                        "🔥 Oversized payload blocked",
                        extra={
                            "param": key,
                            "length": len(value),
                            "path": request.url.path,
                            "ip": request.client.host if request.client else "unknown",
                        },
                    )
                    return PlainTextResponse("Not Found", status_code=404)

                entropy = shannon_entropy(value)
                if entropy > self.ENTROPY_THRESHOLD:
                    logger.critical(
                        "🔥 High entropy payload blocked",
                        extra={
                            "param": key,
                            "entropy": round(entropy, 2),
                            "path": request.url.path,
                            "ip": request.client.host if request.client else "unknown",
                        },
                    )
                    return PlainTextResponse("Not Found", status_code=404)

        return await call_next(request)
