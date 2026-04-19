"""Authentication helpers for the final project."""
from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import settings


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
        )

    if x_api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return x_api_key
