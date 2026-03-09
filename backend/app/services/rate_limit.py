from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class RateLimitRule:
    key_prefix: str
    limit: int
    window_seconds: int


_BUCKETS: dict[str, deque[float]] = {}


def _check(rule: RateLimitRule, client_key: str) -> None:
    now = time.time()
    bucket_key = f"{rule.key_prefix}:{client_key}"
    bucket = _BUCKETS.setdefault(bucket_key, deque())

    while bucket and (now - bucket[0]) > rule.window_seconds:
        bucket.popleft()

    if len(bucket) >= rule.limit:
        retry_after = int(rule.window_seconds - (now - bucket[0])) if bucket else rule.window_seconds
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Rate limit exceeded",
                "retry_after_seconds": max(1, retry_after),
            },
        )

    bucket.append(now)


def rate_limit_dependency(rule: RateLimitRule):
    async def _dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        _check(rule, client_host)

    return _dependency


auth_rate_limit = rate_limit_dependency(RateLimitRule("auth", limit=20, window_seconds=60))
report_rate_limit = rate_limit_dependency(RateLimitRule("report", limit=30, window_seconds=60))
