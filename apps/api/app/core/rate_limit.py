from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import settings

SENSITIVE_PREFIXES = (
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/demo",
    "/api/ai/",
)

_buckets: dict[str, deque[float]] = defaultdict(deque)


def is_rate_limited(request: Request) -> bool:
    if not settings.rate_limit_enabled:
        return False
    path = request.url.path
    if not any(path.startswith(prefix) for prefix in SENSITIVE_PREFIXES):
        return False

    now = time.monotonic()
    window_seconds = max(1, settings.rate_limit_window_seconds)
    limit = max(1, settings.rate_limit_sensitive_per_window)
    key = f"{_client_key(request)}:{path}"
    bucket = _buckets[key]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def reset_rate_limits() -> None:
    _buckets.clear()
