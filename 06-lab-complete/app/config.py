"""12-factor configuration for the final production agent."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str, default: str) -> tuple[str, ...]:
    raw = os.getenv(name, default)
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return tuple(values)


@dataclass(frozen=True)
class Settings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", False))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Production AI Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))

    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://redis:6379/0"))

    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-key-change-me"))
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: _env_csv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        )
    )

    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "mock-llm"))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )
    monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("MONTHLY_BUDGET_USD", "10.0"))
    )

    history_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("HISTORY_TTL_SECONDS", str(30 * 24 * 3600)))
    )
    history_max_messages: int = field(
        default_factory=lambda: int(os.getenv("HISTORY_MAX_MESSAGES", "20"))
    )
    graceful_shutdown_timeout: int = field(
        default_factory=lambda: int(os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", "30"))
    )

    def validate(self) -> "Settings":
        if self.port <= 0:
            raise ValueError("PORT must be > 0")
        if self.rate_limit_per_minute <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be > 0")
        if self.monthly_budget_usd <= 0:
            raise ValueError("MONTHLY_BUDGET_USD must be > 0")
        if self.environment == "production" and self.agent_api_key.startswith("dev-"):
            raise ValueError("AGENT_API_KEY must be set to a non-default value in production")
        return self


settings = Settings().validate()
