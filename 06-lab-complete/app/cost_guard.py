"""Redis-backed monthly budget guard."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from redis import Redis

from app.config import settings

PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.00060
MONTH_TTL_SECONDS = 35 * 24 * 3600


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) * 2)


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
    output_cost = (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
    return round(input_cost + output_cost, 6)


def month_key(user_id: str) -> str:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    return f"budget:{month}:{user_id}"


def get_budget_snapshot(redis_client: Redis, user_id: str) -> dict[str, float | int | str]:
    key = month_key(user_id)
    usage = redis_client.hgetall(key)
    used_usd = float(usage.get("used_usd", 0.0))
    request_count = int(usage.get("request_count", 0))
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    return {
        "user_id": user_id,
        "month": datetime.now(timezone.utc).strftime("%Y-%m"),
        "used_usd": round(used_usd, 6),
        "remaining_usd": round(max(0.0, settings.monthly_budget_usd - used_usd), 6),
        "budget_usd": settings.monthly_budget_usd,
        "request_count": request_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def check_budget(redis_client: Redis, user_id: str, estimated_cost: float) -> dict[str, float | int | str]:
    snapshot = get_budget_snapshot(redis_client, user_id)
    if snapshot["used_usd"] + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": snapshot["used_usd"],
                "estimated_next_cost_usd": estimated_cost,
                "budget_usd": settings.monthly_budget_usd,
            },
        )
    return snapshot


def record_usage(
    redis_client: Redis,
    user_id: str,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, float | int | str]:
    key = month_key(user_id)
    actual_cost = estimate_cost(input_tokens, output_tokens)

    pipe = redis_client.pipeline()
    pipe.hincrbyfloat(key, "used_usd", actual_cost)
    pipe.hincrby(key, "request_count", 1)
    pipe.hincrby(key, "input_tokens", input_tokens)
    pipe.hincrby(key, "output_tokens", output_tokens)
    pipe.expire(key, MONTH_TTL_SECONDS)
    used_usd, request_count, total_input, total_output, _ = pipe.execute()

    return {
        "user_id": user_id,
        "month": datetime.now(timezone.utc).strftime("%Y-%m"),
        "used_usd": round(float(used_usd), 6),
        "remaining_usd": round(max(0.0, settings.monthly_budget_usd - float(used_usd)), 6),
        "budget_usd": settings.monthly_budget_usd,
        "request_count": int(request_count),
        "input_tokens": int(total_input),
        "output_tokens": int(total_output),
    }
