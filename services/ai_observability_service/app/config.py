"""Runtime configuration for the AI Observability Service.

Follows the same convention as the other services' config modules (plain
`os.environ` reads, no configuration framework). Langfuse credentials are
never required to be present — this service must start and serve its
fixed-infrastructure-cost APIs even with observability fully disabled
(see app/langfuse_client.py's "disabled mode").
"""
import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_DB_PATH = "./data/ai_observability.db"
DEFAULT_MAX_EVENTS_PER_BATCH = 100
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LANGFUSE_BASE_URL = "https://cloud.langfuse.com"
DEFAULT_LANGFUSE_ENVIRONMENT = "development"
DEFAULT_LANGFUSE_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class Settings:
    db_path: str
    max_events_per_batch: int
    log_level: str

    # Langfuse — all optional. Observability is considered "enabled" only
    # when both keys are present (see app/langfuse_client.py
    # is_observability_enabled()) — there is no separate on/off flag to
    # keep out of sync with whether credentials actually exist.
    langfuse_public_key: Optional[str]
    langfuse_secret_key: Optional[str]
    langfuse_base_url: str
    langfuse_environment: str
    langfuse_release: Optional[str]
    langfuse_timeout_seconds: float


def load_settings() -> Settings:
    db_path = os.environ.get("AI_OBSERVABILITY_DB_PATH", DEFAULT_DB_PATH)

    raw_max_batch = os.environ.get("MAX_EVENTS_PER_BATCH", str(DEFAULT_MAX_EVENTS_PER_BATCH))
    try:
        max_events_per_batch = int(raw_max_batch)
    except ValueError:
        max_events_per_batch = DEFAULT_MAX_EVENTS_PER_BATCH
    if max_events_per_batch <= 0:
        max_events_per_batch = DEFAULT_MAX_EVENTS_PER_BATCH

    log_level = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL)

    raw_timeout = os.environ.get("LANGFUSE_TIMEOUT_SECONDS", str(DEFAULT_LANGFUSE_TIMEOUT_SECONDS))
    try:
        langfuse_timeout_seconds = float(raw_timeout)
    except ValueError:
        langfuse_timeout_seconds = DEFAULT_LANGFUSE_TIMEOUT_SECONDS

    return Settings(
        db_path=db_path,
        max_events_per_batch=max_events_per_batch,
        log_level=log_level,
        langfuse_public_key=os.environ.get("LANGFUSE_PUBLIC_KEY") or None,
        langfuse_secret_key=os.environ.get("LANGFUSE_SECRET_KEY") or None,
        langfuse_base_url=os.environ.get("LANGFUSE_BASE_URL", DEFAULT_LANGFUSE_BASE_URL),
        langfuse_environment=os.environ.get("LANGFUSE_ENVIRONMENT", DEFAULT_LANGFUSE_ENVIRONMENT),
        langfuse_release=os.environ.get("LANGFUSE_RELEASE") or None,
        langfuse_timeout_seconds=langfuse_timeout_seconds,
    )
