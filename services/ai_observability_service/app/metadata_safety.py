"""Allow-list enforcement for any metadata sent to Langfuse (trace-level or
observation-level).

This is the structural control that keeps metadata from ever becoming a
free-text dump of call content — never a transcript, prompt, customer
name/email/phone, credential, API key, or raw provider response. Only a
small, fixed set of keys — all small structured telemetry signals already
visible elsewhere in this project's own API contracts
(docs/api_contracts.md) — are permitted per context. Anything else is
stripped, not silently accepted and not used to reject the whole
event/trace (a caller sending one extra, disallowed key still gets
everything else recorded; they just don't get that key back).

Values are restricted to primitives (str/int/float/bool/None) or a flat
list of primitives, with a length cap on strings, so a key being on an
allow-list still couldn't be used to smuggle in a full transcript.
"""
from typing import Any

# Per-observation metadata (spans/generations for individual pipeline
# stages — RAG results, signal-analyser flags, error codes, etc.)
OBSERVATION_METADATA_ALLOWED_KEYS = frozenset(
    {
        "filter_requested",
        "filter_applied",
        "dropped_filter_keys",
        "results_returned",
        "results_above_threshold",
        "search_type",
        "knowledge_base_id",
        "decision_maker_present",
        "relevant_services",
        "missing_features",
        "human_review_required",
        "risk_level",
        "http_status",
        "error_code",
        "retry_count",
        "clamped_fields",
        "finish_reason",
        "thinking_enabled",
        "reranker_enabled",
        "initial_top_k",
        "final_top_k",
        "returned_call_ids",
        "similarity_scores",
    }
)

# Trace-level metadata (CLAUDE.md "Approved Observability Data Model") —
# a distinct, deliberately small set: call/execution correlation IDs,
# pipeline outcome, audio duration, and a safe (enum-like) error stage
# name — never a raw error message, which could echo user input.
TRACE_METADATA_ALLOWED_KEYS = frozenset(
    {
        "call_id",
        "n8n_execution_id",
        "workflow_version",
        "audio_duration_seconds",
        "final_status",
        "human_review_required",
        "error_stage",
    }
)

MAX_STRING_VALUE_LENGTH = 200
MAX_LIST_LENGTH = 20


def _is_safe_scalar(value: Any) -> bool:
    if value is None or isinstance(value, (bool, int, float)):
        return True
    if isinstance(value, str):
        return len(value) <= MAX_STRING_VALUE_LENGTH
    return False


def sanitize_metadata(
    raw: Any, allowed_keys: frozenset = OBSERVATION_METADATA_ALLOWED_KEYS
) -> tuple[dict[str, Any], list[str]]:
    """Returns (sanitized_metadata, stripped_keys). Never raises — an
    unsafe, malformed, or disallowed value is stripped, not treated as a
    reason to reject the whole event/trace. `allowed_keys` defaults to the
    per-observation allow-list; pass `TRACE_METADATA_ALLOWED_KEYS` for
    trace-level metadata."""
    if not isinstance(raw, dict):
        return {}, []

    sanitized: dict[str, Any] = {}
    stripped: list[str] = []

    for key, value in raw.items():
        if key not in allowed_keys:
            stripped.append(str(key))
            continue

        if isinstance(value, list):
            if len(value) <= MAX_LIST_LENGTH and all(_is_safe_scalar(v) for v in value):
                sanitized[key] = value
            else:
                stripped.append(str(key))
            continue

        if _is_safe_scalar(value):
            sanitized[key] = value
        else:
            stripped.append(str(key))

    return sanitized, stripped
