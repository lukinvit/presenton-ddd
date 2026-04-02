"""In-memory per-IP rate limiter middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple sliding-window per-IP rate limiter.

    Attributes:
        requests_per_minute: Maximum allowed requests per IP per minute.
    """

    def __init__(self, app, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._window: dict[str, deque[float]] = defaultdict(deque)

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _is_allowed(self, ip: str) -> bool:
        now = time.monotonic()
        cutoff = now - 60.0
        timestamps = self._window[ip]
        # Drop timestamps outside the sliding window
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()
        if len(timestamps) >= self.requests_per_minute:
            return False
        timestamps.append(now)
        return True

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        ip = self._get_client_ip(request)
        if not self._is_allowed(ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests", "retry_after": 60},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
