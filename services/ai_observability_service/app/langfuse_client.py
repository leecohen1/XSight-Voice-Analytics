"""Server-side Langfuse client wrapper.

This module is the ONLY place in this service that touches the Langfuse
SDK directly — every other module works through `ObservabilityClient`.
Two hard guarantees enforced throughout:

1. **Observability failure must never fail call analysis.** Every public
   method here catches every exception, logs it, and returns a safe
   "nothing happened" result (None / empty) rather than raising. A caller
   never needs a try/except around these calls.

2. **"Disabled" is the safe default.** When LANGFUSE_PUBLIC_KEY or
   LANGFUSE_SECRET_KEY is missing, every method becomes a documented
   no-op — this service (and, later, the pipeline that calls it) works
   identically whether or not Langfuse credentials have been configured.
   No real Langfuse account has been created for this project as part of
   this task; every test and every code path here runs with observability
   disabled unless a test explicitly injects a mock client.

Current Langfuse Python SDK: v4 (`langfuse==4.14.1`, confirmed via the
live docs on 2026-07-27 — this project explicitly does not build against
the deprecated v3/legacy API surface). Key current APIs used below:
`get_client()`, `start_as_current_observation(as_type=, name=, model=,
trace_context=)`, `.update(usage_details=, cost_details=, ...)`,
`.update_trace(tags=, metadata=, session_id=, user_id=)`,
`create_trace_id(seed=)`, `create_score(...)`.
"""
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from app.config import Settings
from app.metadata_safety import (
    OBSERVATION_METADATA_ALLOWED_KEYS,
    TRACE_METADATA_ALLOWED_KEYS,
    sanitize_metadata,
)

logger = logging.getLogger("ai_observability_service")


def is_observability_enabled(settings: Settings) -> bool:
    """Enabled iff BOTH keys are present — no separate flag to fall out of
    sync with whether credentials actually exist."""
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


def _local_deterministic_trace_id(seed: str) -> str:
    """A 32-lowercase-hex-char ID derived deterministically from `seed`,
    matching the shape Langfuse's own `create_trace_id` produces (W3C
    Trace Context: 16 bytes / 32 hex chars). Used whenever the real SDK
    isn't available/enabled, so callers always get a stable,
    correlation-safe ID regardless of observability state — the same
    `call_id` always maps to the same trace ID, enabled or not."""
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


@dataclass
class StageResult:
    """One already-finished pipeline-stage observation to record under a
    trace. `kind` is "span" or "generation" — deterministic services
    (guardrails, RAG, signal analysis, LangGraph reasoning, routing) are
    always "span"; only real LLM calls are "generation". Passing
    kind="generation" for a stage with no model is a caller error and is
    downgraded to "span" defensively (never mis-record a deterministic
    step as a priced generation)."""

    name: str
    kind: str  # "span" | "generation"
    status: str = "success"  # "success" | "failed" | "partial"
    model: Optional[str] = None
    input: Optional[Any] = None
    output: Optional[Any] = None
    usage_details: Optional[dict[str, int]] = None
    cost_details: Optional[dict[str, str]] = None  # Decimal-as-string, never float
    latency_ms: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceIngestResult:
    trace_id: str
    enabled: bool
    recorded_stage_names: list[str]
    failed_stage_names: list[str]


class ObservabilityClient:
    """Wraps a real (or mocked, in tests) Langfuse client instance.
    `client` is `None` whenever observability is disabled — every method
    checks this first and no-ops."""

    def __init__(self, client: Any, enabled: bool):
        self._client = client
        self.enabled = enabled

    def create_trace_id(self, seed: str) -> str:
        if self.enabled and self._client is not None:
            try:
                return self._client.create_trace_id(seed=seed)
            except Exception:
                logger.exception("Langfuse create_trace_id failed for seed=%r; using local fallback", seed)
        return _local_deterministic_trace_id(seed)

    def record_span(
        self,
        *,
        trace_id: str,
        name: str,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        metadata: Optional[dict] = None,
        status: str = "success",
    ) -> Optional[str]:
        """Creates one complete span observation nested under `trace_id`
        (auto-nests under whatever parent observation is currently active
        on this thread, per the SDK's context-stack model — see module
        docstring). Returns the observation ID, or None if disabled or on
        any error. Never raises."""
        if not self.enabled or self._client is None:
            return None
        try:
            sanitized_metadata, _ = sanitize_metadata(metadata or {}, OBSERVATION_METADATA_ALLOWED_KEYS)
            with self._client.start_as_current_observation(
                as_type="span", name=name, trace_context={"trace_id": trace_id}
            ) as span:
                span.update(
                    input=input,
                    output=output,
                    metadata=sanitized_metadata,
                    level="ERROR" if status == "failed" else "DEFAULT",
                )
                return getattr(span, "id", None)
        except Exception:
            logger.exception("Langfuse record_span failed for stage '%s'", name)
            return None

    def record_generation(
        self,
        *,
        trace_id: str,
        name: str,
        model: str,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        usage_details: Optional[dict[str, int]] = None,
        cost_details: Optional[dict[str, str]] = None,
        metadata: Optional[dict] = None,
        status: str = "success",
    ) -> Optional[str]:
        """Creates one complete generation observation. `usage_details` and
        `cost_details` are passed through EXACTLY as given — this wrapper
        never fabricates a value for either; a caller with no measured
        usage must pass `usage_details=None`, never a zero-filled dict."""
        if not self.enabled or self._client is None:
            return None
        try:
            sanitized_metadata, _ = sanitize_metadata(metadata or {}, OBSERVATION_METADATA_ALLOWED_KEYS)
            with self._client.start_as_current_observation(
                as_type="generation", name=name, model=model, trace_context={"trace_id": trace_id}
            ) as generation:
                generation.update(
                    input=input,
                    output=output,
                    usage_details=usage_details,
                    cost_details=cost_details,
                    metadata=sanitized_metadata,
                    level="ERROR" if status == "failed" else "DEFAULT",
                )
                return getattr(generation, "id", None)
        except Exception:
            logger.exception("Langfuse record_generation failed for stage '%s' (model=%s)", name, model)
            return None

    def update_trace_attributes(
        self,
        *,
        trace_id: str,
        name: str,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Sets trace-level fields (as opposed to a single observation's
        own input/output). Must be called from within the trace's root
        span context. Returns True iff it succeeded; never raises."""
        if not self.enabled or self._client is None:
            return False
        try:
            sanitized_metadata, _ = sanitize_metadata(metadata or {}, TRACE_METADATA_ALLOWED_KEYS)
            self._client.update_current_trace(
                name=name, tags=tags or [], metadata=sanitized_metadata, session_id=session_id, user_id=user_id
            )
            return True
        except Exception:
            logger.exception("Langfuse update_trace_attributes failed for trace_id=%s", trace_id)
            return False

    def create_score(
        self,
        *,
        name: str,
        value: Any,
        data_type: str,
        trace_id: str,
        observation_id: Optional[str] = None,
        score_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> bool:
        """`score_id` is the idempotency key — passing the same score_id
        twice must not create a duplicate score (Langfuse upserts by ID).
        Returns True iff the call was made without error; never raises."""
        if not self.enabled or self._client is None:
            return False
        try:
            self._client.create_score(
                name=name,
                value=value,
                data_type=data_type,
                trace_id=trace_id,
                observation_id=observation_id,
                score_id=score_id,
                comment=comment,
            )
            return True
        except Exception:
            logger.exception("Langfuse create_score failed for name=%s trace_id=%s", name, trace_id)
            return False

    def flush(self, timeout_seconds: float) -> None:
        """Bounded flush — never allowed to hang the caller. `timeout_seconds`
        is honored on a best-effort basis by whatever the underlying SDK
        supports; failures are logged, never raised."""
        if not self.enabled or self._client is None:
            return
        try:
            self._client.flush()
        except Exception:
            logger.exception("Langfuse flush failed (continuing without blocking the caller)")


def build_observability_client(settings: Settings) -> ObservabilityClient:
    """Factory used by the FastAPI dependency (see app/main.py). Only
    imports and constructs the real `langfuse` SDK client when both keys
    are present — when disabled, no Langfuse import happens at all on this
    path, so a completely credential-free environment (e.g. this task's
    own development/test environment) never touches the SDK's network
    layer in any way."""
    if not is_observability_enabled(settings):
        return ObservabilityClient(client=None, enabled=False)

    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_base_url,
            environment=settings.langfuse_environment,
            release=settings.langfuse_release,
            timeout=settings.langfuse_timeout_seconds,
        )
        return ObservabilityClient(client=client, enabled=True)
    except Exception:
        logger.exception("Failed to construct the Langfuse client; falling back to disabled mode")
        return ObservabilityClient(client=None, enabled=False)
