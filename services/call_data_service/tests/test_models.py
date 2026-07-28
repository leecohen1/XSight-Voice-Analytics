"""Record schema, enum, ID and normalization validation."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models import (
    AnalyzedCallRecord,
    Attention,
    CallAnalysis,
    CreateCallRequest,
    is_valid_call_id,
    normalize_agent_name,
)


def _base(**overrides):
    payload = {
        "call_id": "CALL_001",
        "source": "historical_seed",
        "created_at": datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        "agent_name": "Sarah Levi",
        "status": "completed",
        "analysis": CallAnalysis(),
    }
    payload.update(overrides)
    return payload


# ---- call_id validation ----------------------------------------------------


@pytest.mark.parametrize("call_id", ["CALL_001", "CALL_024", "CALL_999"])
def test_historical_call_ids_are_valid(call_id):
    assert is_valid_call_id(call_id)
    assert AnalyzedCallRecord(**_base(call_id=call_id)).call_id == call_id


def test_live_call_id_with_uuid_is_valid():
    call_id = "CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c"
    assert is_valid_call_id(call_id)
    assert AnalyzedCallRecord(**_base(call_id=call_id)).call_id == call_id


@pytest.mark.parametrize(
    "call_id",
    [
        "XS-1001",            # the retired frontend-generated scheme
        "CALL_1",             # too few digits
        "CALL_0001",          # too many digits
        "call_001",           # wrong case on the prefix
        "CALL_not-a-uuid",
        "",
        "CALL_3f2b9c1a4d5e4f6a8b7c9d0e1f2a3b4c",  # uuid without hyphens
    ],
)
def test_invalid_call_ids_are_rejected(call_id):
    assert not is_valid_call_id(call_id)
    with pytest.raises(ValidationError):
        AnalyzedCallRecord(**_base(call_id=call_id))


def test_create_request_rejects_frontend_generated_id():
    with pytest.raises(ValidationError):
        CreateCallRequest(call_id="XS-1004", agent_name="Sarah Levi", analysis=CallAnalysis())


# ---- enums -----------------------------------------------------------------


@pytest.mark.parametrize("status", ["completed", "flagged", "human_review_required"])
def test_allowed_statuses(status):
    assert AnalyzedCallRecord(**_base(status=status)).status == status


@pytest.mark.parametrize("status", ["failed", "uploaded", "analyzing", "COMPLETED"])
def test_disallowed_statuses_are_rejected(status):
    with pytest.raises(ValidationError):
        AnalyzedCallRecord(**_base(status=status))


@pytest.mark.parametrize("source", ["historical_seed", "live_analysis"])
def test_allowed_sources(source):
    assert AnalyzedCallRecord(**_base(source=source)).source == source


def test_disallowed_source_is_rejected():
    with pytest.raises(ValidationError):
        AnalyzedCallRecord(**_base(source="manual_entry"))


@pytest.mark.parametrize("priority", ["low", "medium", "high", "critical"])
def test_allowed_attention_priorities(priority):
    assert Attention(priority=priority).priority == priority


def test_disallowed_attention_priority_is_rejected():
    with pytest.raises(ValidationError):
        Attention(priority="urgent")


@pytest.mark.parametrize(
    "category",
    [
        "recoverable_opportunity",
        "human_review",
        "customer_dissatisfaction",
        "critical_coaching",
        "evidence_conflict",
        "low_priority",
    ],
)
def test_allowed_attention_categories(category):
    assert Attention(category=category).category == category


def test_disallowed_attention_category_is_rejected():
    with pytest.raises(ValidationError):
        Attention(category="needs_followup")


def test_priority_score_is_bounded():
    with pytest.raises(ValidationError):
        Attention(priority_score=101)
    with pytest.raises(ValidationError):
        Attention(priority_score=-1)


@pytest.mark.parametrize("score", [0, 6, -1])
def test_out_of_range_scores_are_rejected(score):
    with pytest.raises(ValidationError):
        CallAnalysis(agent_performance_score=score)


def test_confidence_bounds_enforced():
    with pytest.raises(ValidationError):
        CallAnalysis(confidence=1.5)
    assert CallAnalysis(confidence=None).confidence is None


# ---- agent name normalization ---------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Sarah Levi", "sarah levi"),
        ("  Sarah Levi  ", "sarah levi"),
        ("SARAH   LEVI", "sarah levi"),
        ("sarah\tlevi", "sarah levi"),
    ],
)
def test_normalize_agent_name(raw, expected):
    assert normalize_agent_name(raw) == expected


def test_record_derives_normalized_name_and_keeps_display_name():
    record = AnalyzedCallRecord(**_base(agent_name="  SARAH   Levi "))
    assert record.agent_name == "SARAH Levi"       # collapsed, casing preserved
    assert record.agent_name_normalized == "sarah levi"


def test_record_ignores_caller_supplied_normalized_name():
    """A caller cannot split an agent's aggregates by sending a bogus key."""
    record = AnalyzedCallRecord(**_base(agent_name="Sarah Levi", agent_name_normalized="someone else"))
    assert record.agent_name_normalized == "sarah levi"


def test_empty_agent_name_is_rejected():
    with pytest.raises(ValidationError):
        AnalyzedCallRecord(**_base(agent_name="   "))


# ---- timestamps ------------------------------------------------------------


def test_naive_created_at_is_read_as_utc():
    record = AnalyzedCallRecord(**_base(created_at=datetime(2026, 7, 1, 9, 0)))
    assert record.created_at.tzinfo is not None
    assert record.created_at == datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)


# ---- unknown values are null, never fabricated -----------------------------


def test_unknown_analysis_fields_default_to_null_not_zero():
    analysis = CallAnalysis()
    assert analysis.confidence is None
    assert analysis.risk_level is None
    assert analysis.agent_performance_score is None
    assert analysis.lead_quality_score is None
    assert analysis.similar_calls == []
    assert analysis.coaching_feedback == []
    assert analysis.detected_signals == []


def test_extra_pipeline_fields_do_not_break_an_existing_record():
    """A future additive field must not make already-stored objects unreadable."""
    record = AnalyzedCallRecord.model_validate(
        {**_base(), "analysis": {"call_summary": "x", "some_future_field": 123}, "unexpected_top_level": True}
    )
    assert record.analysis.call_summary == "x"
