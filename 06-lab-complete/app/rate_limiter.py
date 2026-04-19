"""Redis-backed sliding window rate limiter."""
from __future__ import annotations

import time
import uuid

from fastapi import HTTPException
from redis import Redis

from app.config import settings

WINDOW_SECONDS = 60


def check_rate_limit(redis_client: Redis, user_id: str) -> dict[str, int]:
    key = f"rate_limit:{user_id}"
    now = time.time()
    window_start = now - WINDOW_SECONDS

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, "-inf", window_start)
    pipe.zcard(key)
    pipe.zrange(key, 0, 0, withscores=True)
    _, current_count, oldest_entry = pipe.execute()

    if current_count >= settings.rate_limit_per_minute:
        retry_after = WINDOW_SECONDS
        if oldest_entry:
            oldest_timestamp = oldest_entry[0][1]
            retry_after = max(1, int(oldest_timestamp + WINDOW_SECONDS - now) + 1)

        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": settings.rate_limit_per_minute,
                "window_seconds": WINDOW_SECONDS,
                "retry_after_seconds": retry_after,
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                "X-RateLimit-Remaining": "0",
            },
        )

    member = f"{now:.6f}:{uuid.uuid4().hex}"
    pipe = redis_client.pipeline()
    pipe.zadd(key, {member: now})
    pipe.expire(key, WINDOW_SECONDS + 1)
    pipe.execute()

    remaining = max(0, settings.rate_limit_per_minute - (current_count + 1))
    return {
        "limit": settings.rate_limit_per_minute,
        "remaining": remaining,
        "window_seconds": WINDOW_SECONDS,
    }
