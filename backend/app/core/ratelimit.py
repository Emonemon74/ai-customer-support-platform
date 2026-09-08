"""Minimal fixed-window rate limiting.

In-process (per worker) -- good enough to blunt credential-stuffing and abusive
bursts on a single box. A Redis-backed limiter is the next step for a
multi-instance deployment.
"""

import threading
import time

from fastapi import HTTPException, Request, status

from app.core.settings import settings


class _FixedWindow:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, tuple[int, float]] = {}

    def check(self, key: str, limit: int, window: float) -> bool:
        now = time.time()
        with self._lock:
            count, window_start = self._hits.get(key, (0, now))

            if now - window_start >= window:
                count, window_start = 0, now

            count += 1
            self._hits[key] = (count, window_start)
            return count <= limit


_store = _FixedWindow()


def _client_key(request: Request, scope: str) -> str:
    client = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client = forwarded.split(",")[0].strip()
    return f"{scope}:{client}"


class RateLimiter:
    """FastAPI dependency: ``Depends(RateLimiter("auth", per_minute=10))``."""

    def __init__(self, scope: str, per_minute: int):
        self.scope = scope
        self.per_minute = per_minute

    def __call__(self, request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        allowed = _store.check(
            _client_key(request, self.scope),
            limit=self.per_minute,
            window=60.0,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again shortly.",
            )
