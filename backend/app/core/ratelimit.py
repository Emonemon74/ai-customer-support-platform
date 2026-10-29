"""Minimal fixed-window rate limiting.

In-process (per worker) -- good enough to blunt credential-stuffing and abusive
bursts on a single box. A Redis-backed limiter is the next step for a
multi-instance deployment.
"""

import threading
import time

from fastapi import HTTPException, Request, status

from app.core.settings import settings

# Above this many tracked keys, expired windows are dropped so the table can't
# grow without bound under a flood of distinct client addresses.
_PRUNE_THRESHOLD = 10_000


class _FixedWindow:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, tuple[int, float, float]] = {}

    def check(self, key: str, limit: int, window: float) -> bool:
        now = time.time()
        with self._lock:
            if len(self._hits) > _PRUNE_THRESHOLD:
                self._hits = {
                    k: v for k, v in self._hits.items() if now - v[1] < v[2]
                }

            count, window_start, _ = self._hits.get(key, (0, now, window))

            if now - window_start >= window:
                count, window_start = 0, now

            count += 1
            self._hits[key] = (count, window_start, window)
            return count <= limit


_store = _FixedWindow()


def _client_key(request: Request, scope: str) -> str:
    client = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client = forwarded.split(",")[0].strip()
    return f"{scope}:{client}"


class RateLimiter:
    """FastAPI dependency: ``Depends(RateLimiter("auth", per_minute=10))``.

    ``per_day`` instead gives a 24-hour window per client address; a limit of 0
    disables it.
    """

    def __init__(
        self,
        scope: str,
        per_minute: int | None = None,
        per_day: int | None = None,
    ):
        if (per_minute is None) == (per_day is None):
            raise ValueError("pass exactly one of per_minute or per_day")
        self.scope = scope
        self.limit = per_minute if per_minute is not None else per_day
        self.window = 60.0 if per_minute is not None else 86400.0

    def __call__(self, request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED or not self.limit:
            return

        allowed = _store.check(
            _client_key(request, self.scope),
            limit=self.limit,
            window=self.window,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again shortly.",
            )
