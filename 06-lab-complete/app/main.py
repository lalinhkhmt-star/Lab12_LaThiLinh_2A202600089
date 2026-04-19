"""
Production-ready AI agent for Day 12.

This app combines:
- 12-factor configuration
- API key authentication
- Redis-backed rate limiting
- Redis-backed monthly budget guard
- Redis-backed conversation history
- Health/readiness probes
- Graceful shutdown
- Structured JSON logging
"""
from __future__ import annotations

import json
import logging
import os
import signal
import socket
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from redis import Redis
from redis.exceptions import RedisError

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import (
    check_budget,
    estimate_cost,
    estimate_tokens,
    get_budget_snapshot,
    record_usage,
)
from app.rate_limiter import check_rate_limit
from utils.mock_llm import ask as llm_ask

logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO), format="%(message)s")
logger = logging.getLogger("production-agent")

INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname())
START_TIME = time.time()
_redis_client: Redis | None = None
_is_ready = False
_accepting_requests = True
_active_requests = 0
_request_count = 0
_error_count = 0


def log_event(level: int, event: str, **fields: object) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "lvl": logging.getLevelName(level),
        "event": event,
        "instance_id": INSTANCE_ID,
        **fields,
    }
    logger.log(level, json.dumps(payload, ensure_ascii=False))


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis_client


def require_redis() -> Redis:
    try:
        client = get_redis_client()
        client.ping()
        return client
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Redis is not available") from exc


def history_key(user_id: str) -> str:
    return f"history:{user_id}"


def load_history(redis_client: Redis, user_id: str) -> list[dict[str, str]]:
    raw_messages = redis_client.lrange(history_key(user_id), -settings.history_max_messages, -1)
    history: list[dict[str, str]] = []
    for item in raw_messages:
        try:
            history.append(json.loads(item))
        except json.JSONDecodeError:
            continue
    return history


def append_history(redis_client: Redis, user_id: str, role: str, content: str) -> None:
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    key = history_key(user_id)
    pipe = redis_client.pipeline()
    pipe.rpush(key, json.dumps(message, ensure_ascii=False))
    pipe.ltrim(key, -settings.history_max_messages, -1)
    pipe.expire(key, settings.history_ttl_seconds)
    pipe.execute()


def build_prompt(history: list[dict[str, str]], question: str) -> str:
    if not history:
        return question

    recent_context = history[-4:]
    conversation = "\n".join(f"{item['role']}: {item['content']}" for item in recent_context)
    return f"Conversation history:\n{conversation}\nCurrent user question: {question}"


def install_signal_handlers() -> None:
    def _handle_signal(signum: int, _frame: object) -> None:
        global _accepting_requests, _is_ready
        _accepting_requests = False
        _is_ready = False
        log_event(logging.INFO, "signal_received", signum=signum, active_requests=_active_requests)

    for signal_name in ("SIGTERM", "SIGINT"):
        if hasattr(signal, signal_name):
            signal.signal(getattr(signal, signal_name), _handle_signal)


install_signal_handlers()


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _is_ready, _accepting_requests
    _accepting_requests = True
    log_event(
        logging.INFO,
        "startup",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    try:
        client = get_redis_client()
        client.ping()
        _is_ready = True
        log_event(logging.INFO, "redis_connected", redis_url=settings.redis_url)
    except RedisError as exc:
        _is_ready = False
        log_event(logging.ERROR, "redis_connection_failed", error=str(exc))

    try:
        yield
    finally:
        global _redis_client
        _is_ready = False
        _accepting_requests = False
        if _redis_client is not None:
            _redis_client.close()
            _redis_client = None
        log_event(logging.INFO, "shutdown", active_requests=_active_requests)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    global _active_requests, _request_count, _error_count

    if not _accepting_requests and request.url.path not in {"/health", "/ready"}:
        return JSONResponse(
            status_code=503,
            content={"detail": "Server is shutting down and not accepting new requests"},
        )

    start = time.perf_counter()
    _active_requests += 1
    _request_count += 1

    try:
        response: Response = await call_next(request)
    except Exception as exc:
        _error_count += 1
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        log_event(
            logging.ERROR,
            "request_failed",
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
            error=str(exc),
        )
        raise
    finally:
        _active_requests -= 1

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Instance-Id"] = INSTANCE_ID
    if "server" in response.headers:
        del response.headers["server"]

    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    log_event(
        logging.INFO,
        "request_completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    return response


class AskRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="Stable identifier for rate limiting and cost tracking",
    )
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    model: str
    turn: int
    history_length: int
    rate_limit_remaining: int
    budget_used_usd: float
    budget_remaining_usd: float
    served_by: str
    timestamp: str


@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": INSTANCE_ID,
        "endpoints": {
            "health": "GET /health",
            "ready": "GET /ready",
            "ask": "POST /ask",
            "history": "GET /history/{user_id}",
            "metrics": "GET /metrics",
        },
    }


@app.get("/health", tags=["Operations"])
def health():
    redis_ok = False
    try:
        get_redis_client().ping()
        redis_ok = True
    except RedisError:
        redis_ok = False

    return {
        "status": "ok",
        "redis_connected": redis_ok,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "instance_id": INSTANCE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    if not _accepting_requests:
        raise HTTPException(status_code=503, detail="Server is shutting down")

    try:
        get_redis_client().ping()
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Redis is not ready") from exc

    return {"status": "ready", "instance_id": INSTANCE_ID}


@app.get("/history/{user_id}", tags=["Agent"])
def get_history(user_id: str, _api_key: str = Depends(verify_api_key)):
    redis_client = require_redis()
    history = load_history(redis_client, user_id)
    return {
        "user_id": user_id,
        "history_length": len(history),
        "messages": history,
    }


@app.get("/metrics", tags=["Operations"])
def metrics(_api_key: str = Depends(verify_api_key)):
    return {
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "request_count": _request_count,
        "error_count": _error_count,
        "active_requests": _active_requests,
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
def ask_agent(body: AskRequest, _api_key: str = Depends(verify_api_key)):
    redis_client = require_redis()

    rate_limit_state = check_rate_limit(redis_client, body.user_id)
    history = load_history(redis_client, body.user_id)

    prompt = build_prompt(history, body.question)
    estimated_input_tokens = estimate_tokens(prompt)
    estimated_output_tokens = 80
    estimated_cost = estimate_cost(estimated_input_tokens, estimated_output_tokens)
    check_budget(redis_client, body.user_id, estimated_cost)

    answer = llm_ask(prompt)

    append_history(redis_client, body.user_id, "user", body.question)
    append_history(redis_client, body.user_id, "assistant", answer)

    actual_input_tokens = estimate_tokens(prompt)
    actual_output_tokens = estimate_tokens(answer)
    budget_state = record_usage(redis_client, body.user_id, actual_input_tokens, actual_output_tokens)
    updated_history = load_history(redis_client, body.user_id)

    log_event(
        logging.INFO,
        "agent_response",
        user_id=body.user_id,
        history_length=len(updated_history),
        budget_used_usd=budget_state["used_usd"],
    )

    return AskResponse(
        user_id=body.user_id,
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        turn=max(1, len([item for item in updated_history if item["role"] == "user"])),
        history_length=len(updated_history),
        rate_limit_remaining=rate_limit_state["remaining"],
        budget_used_usd=budget_state["used_usd"],
        budget_remaining_usd=budget_state["remaining_usd"],
        served_by=INSTANCE_ID,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/usage/{user_id}", tags=["Agent"])
def usage(user_id: str, _api_key: str = Depends(verify_api_key)):
    redis_client = require_redis()
    snapshot = get_budget_snapshot(redis_client, user_id)
    return snapshot


if __name__ == "__main__":
    log_event(
        logging.INFO,
        "uvicorn_start",
        host=settings.host,
        port=settings.port,
        graceful_shutdown_timeout=settings.graceful_shutdown_timeout,
    )
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=settings.graceful_shutdown_timeout,
    )
