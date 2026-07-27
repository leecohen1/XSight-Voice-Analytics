"""Unit tests for app/validation.py — pure function, no DB involved."""
from app.validation import validate_event

VALID_EVENT = {
    "idempotency_key": "exec-1:information_extraction",
    "provider": "gemini",
    "service": "generative_ai",
    "model": "gemini-test-model",
    "pipeline_stage": "information_extraction",
    "use_case": "analyze_sales_call",
    "input_tokens": 501,
    "output_tokens": 30,
    "total_tokens": 531,
    "audio_duration_seconds": None,
    "request_count": 1,
    "latency_ms": 840,
    "status": "success",
    "occurred_at": "2026-07-27T12:00:00Z",
    "metadata": {},
}


def test_valid_event_passes():
    validated, reasons = validate_event(VALID_EVENT)
    assert reasons == []
    assert validated is not None
    assert validated.input_tokens == 501
    assert validated.total_tokens == 531
    # normalized to UTC, "+00:00" suffix, whole-second precision
    assert validated.occurred_at_utc == "2026-07-27T12:00:00+00:00"


def test_negative_input_tokens_rejected():
    event = {**VALID_EVENT, "input_tokens": -5}
    validated, reasons = validate_event(event)
    assert validated is None
    assert any("input_tokens" in r and "negative" in r for r in reasons)


def test_negative_audio_duration_rejected():
    event = {**VALID_EVENT, "audio_duration_seconds": -1.5}
    validated, reasons = validate_event(event)
    assert validated is None
    assert any("audio_duration_seconds" in r and "negative" in r for r in reasons)


def test_negative_latency_rejected():
    event = {**VALID_EVENT, "latency_ms": -100}
    validated, reasons = validate_event(event)
    assert validated is None
    assert any("latency_ms" in r for r in reasons)


def test_inconsistent_total_tokens_rejected():
    event = {**VALID_EVENT, "input_tokens": 500, "output_tokens": 30, "total_tokens": 999}
    validated, reasons = validate_event(event)
    assert validated is None
    assert any("total_tokens" in r for r in reasons)


def test_total_tokens_auto_computed_when_omitted():
    event = {**VALID_EVENT}
    del event["total_tokens"]
    validated, reasons = validate_event(event)
    assert reasons == []
    assert validated.total_tokens == 531


def test_missing_required_field_rejected():
    event = {**VALID_EVENT}
    del event["provider"]
    validated, reasons = validate_event(event)
    assert validated is None
    assert any("provider" in r for r in reasons)


def test_invalid_status_rejected():
    event = {**VALID_EVENT, "status": "bogus"}
    validated, reasons = validate_event(event)
    assert validated is None
    assert any("status" in r for r in reasons)


def test_non_token_based_event_allows_null_tokens():
    """A non-token-based stage (e.g. Call Signal Analyser today) — missing
    token counts must be accepted as 'not applicable', never coerced to 0."""
    event = {
        **VALID_EVENT,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "pipeline_stage": "call_signal_analysis",
        "provider": "internal",
        "service": "call_signal_analyser",
    }
    validated, reasons = validate_event(event)
    assert reasons == []
    assert validated.input_tokens is None
    assert validated.output_tokens is None
    assert validated.total_tokens is None


def test_malformed_event_type_rejected():
    validated, reasons = validate_event("not a dict")  # type: ignore[arg-type]
    assert validated is None
    assert reasons == ["event must be a JSON object"]


def test_invalid_occurred_at_rejected():
    event = {**VALID_EVENT, "occurred_at": "not-a-timestamp"}
    validated, reasons = validate_event(event)
    assert validated is None
    assert any("occurred_at" in r for r in reasons)


def test_occurred_at_with_offset_normalized_to_utc():
    event = {**VALID_EVENT, "occurred_at": "2026-07-27T15:00:00+03:00"}
    validated, reasons = validate_event(event)
    assert reasons == []
    assert validated.occurred_at_utc == "2026-07-27T12:00:00+00:00"
