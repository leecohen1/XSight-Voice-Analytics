"""Manual, per-event validation and normalization.

Each event in a batch is validated independently here (not via a strict
Pydantic model — see app/models.py's docstring for why), so one malformed
event yields a per-item rejection reason instead of a whole-batch 422.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

REQUIRED_STRING_FIELDS = ("idempotency_key", "provider", "service", "pipeline_stage", "use_case", "status", "occurred_at")
NULLABLE_INT_FIELDS = ("input_tokens", "output_tokens", "total_tokens", "request_count", "latency_ms")
NULLABLE_NUMERIC_FIELDS = ("audio_duration_seconds",)

VALID_STATUSES = frozenset({"success", "failed", "partial"})


@dataclass
class ValidatedEvent:
    idempotency_key: str
    provider: str
    service: str
    model: Optional[str]
    pipeline_stage: str
    use_case: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    audio_duration_seconds: Optional[float]
    request_count: Optional[int]
    latency_ms: Optional[int]
    status: str
    occurred_at_utc: str  # normalized ISO 8601, UTC, "...+00:00"
    metadata_raw: Any


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_event(raw: dict) -> tuple[Optional[ValidatedEvent], list[str]]:
    """Validates and normalizes one event dict. Returns (validated_or_None,
    reasons) — reasons is empty iff validation succeeded. Never raises."""
    reasons: list[str] = []

    if not isinstance(raw, dict):
        return None, ["event must be a JSON object"]

    for field in REQUIRED_STRING_FIELDS:
        value = raw.get(field)
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"{field} is required and must be a non-empty string")

    status = raw.get("status")
    if isinstance(status, str) and status not in VALID_STATUSES:
        reasons.append(f"status must be one of {sorted(VALID_STATUSES)}")

    for field in NULLABLE_INT_FIELDS:
        value = raw.get(field)
        if value is not None:
            if not _is_number(value):
                reasons.append(f"{field} must be a number or null")
            elif value < 0:
                reasons.append(f"{field} must not be negative")

    for field in NULLABLE_NUMERIC_FIELDS:
        value = raw.get(field)
        if value is not None:
            if not _is_number(value):
                reasons.append(f"{field} must be a number or null")
            elif value < 0:
                reasons.append(f"{field} must not be negative")

    input_tokens = raw.get("input_tokens")
    output_tokens = raw.get("output_tokens")
    total_tokens = raw.get("total_tokens")
    if (
        isinstance(input_tokens, (int, float))
        and isinstance(output_tokens, (int, float))
        and isinstance(total_tokens, (int, float))
        and not isinstance(input_tokens, bool)
        and not isinstance(output_tokens, bool)
        and not isinstance(total_tokens, bool)
    ):
        if total_tokens != input_tokens + output_tokens:
            reasons.append("total_tokens must equal input_tokens + output_tokens when all three are provided")

    occurred_at_raw = raw.get("occurred_at")
    occurred_at_utc: Optional[str] = None
    if isinstance(occurred_at_raw, str) and occurred_at_raw.strip():
        try:
            parsed = datetime.fromisoformat(occurred_at_raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            # Truncate to whole-second precision before formatting. Sub-second
            # granularity isn't needed for usage telemetry, and a *fixed*
            # format is required for safe lexicographic date-range filtering
            # in SQL: a stray microsecond component (".500000") sorts *after*
            # the "+00:00" suffix in ASCII ('.' > '+'), which would silently
            # misorder same-second timestamps if some events had microseconds
            # and others didn't.
            occurred_at_utc = parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        except ValueError:
            reasons.append("occurred_at must be a valid ISO 8601 timestamp")

    if reasons:
        return None, reasons

    # Auto-compute total_tokens if omitted but both parts are present.
    if total_tokens is None and isinstance(input_tokens, (int, float)) and isinstance(output_tokens, (int, float)):
        total_tokens = input_tokens + output_tokens

    return (
        ValidatedEvent(
            idempotency_key=raw["idempotency_key"],
            provider=raw["provider"],
            service=raw["service"],
            model=raw.get("model") if isinstance(raw.get("model"), str) else None,
            pipeline_stage=raw["pipeline_stage"],
            use_case=raw["use_case"],
            input_tokens=int(input_tokens) if isinstance(input_tokens, (int, float)) else None,
            output_tokens=int(output_tokens) if isinstance(output_tokens, (int, float)) else None,
            total_tokens=int(total_tokens) if isinstance(total_tokens, (int, float)) else None,
            audio_duration_seconds=float(raw["audio_duration_seconds"]) if isinstance(raw.get("audio_duration_seconds"), (int, float)) else None,
            request_count=int(raw["request_count"]) if isinstance(raw.get("request_count"), (int, float)) and not isinstance(raw.get("request_count"), bool) else None,
            latency_ms=int(raw["latency_ms"]) if isinstance(raw.get("latency_ms"), (int, float)) and not isinstance(raw.get("latency_ms"), bool) else None,
            status=raw["status"],
            occurred_at_utc=occurred_at_utc,
            metadata_raw=raw.get("metadata"),
        ),
        [],
    )
