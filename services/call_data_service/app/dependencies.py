"""Dependency wiring.

The repository is resolved through a FastAPI dependency so the whole test
suite can swap in an in-memory S3 fake via `app.dependency_overrides` --
no test ever touches the network or needs AWS credentials.

Settings and the boto3 client are cached per process (they are immutable and
thread-safe) rather than rebuilt per request, matching how rag_service reads
its configuration once at module level.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import Settings, load_settings
from app.repository import CallRepository, build_s3_client


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Raises ConfigurationError (-> 503) when required env vars are absent."""
    return load_settings()


@lru_cache(maxsize=1)
def _cached_repository() -> CallRepository:
    settings = get_settings()
    return CallRepository(s3_client=build_s3_client(settings), settings=settings)


def get_repository() -> CallRepository:
    return _cached_repository()


def reset_caches() -> None:
    """Drop cached settings/client. Used by tests that change environment
    variables between cases."""
    get_settings.cache_clear()
    _cached_repository.cache_clear()
