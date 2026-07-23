"""Unit tests for the deterministic Bedrock filter builder (app/filters.py).

Tested against the real services/rag_service/ingestion/metadata_schema.json
(not a stub) — this is the same file the ingestion pipeline and this service
both depend on being the single source of truth, so testing against a fake
copy would risk the test suite passing while the real schema disagrees.
"""
from app.filters import build_filter, load_filter_allowlist


def test_allowlist_matches_documented_11_fields():
    allowlist = load_filter_allowlist()
    assert set(allowlist.keys()) == {
        "customer_segment", "industry", "main_objection", "customer_intent", "customer_sentiment",
        "sale_result", "call_category", "closing_attempt",
        "follow_up_needed", "next_meeting_scheduled", "decision_maker_present",
    }


def test_no_filters_supplied_returns_none():
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter(None, allowlist)
    assert bedrock_filter is None
    assert applied is None
    assert dropped == []


def test_empty_dict_returns_none():
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter({}, allowlist)
    assert bedrock_filter is None
    assert applied is None
    assert dropped == []


def test_single_allowed_filter_builds_equals_clause():
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter({"main_objection": "price"}, allowlist)
    assert bedrock_filter == {"equals": {"key": "main_objection", "value": "price"}}
    assert applied == "main_objection"
    assert dropped == []


def test_boolean_filter_field():
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter({"follow_up_needed": True}, allowlist)
    assert bedrock_filter == {"equals": {"key": "follow_up_needed", "value": True}}
    assert applied == "follow_up_needed"


def test_unsupported_key_is_dropped_not_rejected():
    """A field not in the allowlist (e.g. an analytical-evidence field, or a
    made-up key) never raises — it's reported as dropped and retrieval
    proceeds semantically."""
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter({"agent_performance_score": 5}, allowlist)
    assert bedrock_filter is None
    assert applied is None
    assert dropped == ["agent_performance_score"]


def test_nonexistent_key_is_dropped():
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter({"not_a_real_field": "x"}, allowlist)
    assert bedrock_filter is None
    assert dropped == ["not_a_real_field"]


def test_invalid_enum_value_is_dropped():
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter({"main_objection": "not_a_valid_objection"}, allowlist)
    assert bedrock_filter is None
    assert dropped == ["main_objection"]


def test_at_most_one_filter_is_ever_applied():
    """Small-Corpus Filter Policy: never combine multiple restrictive
    filters. The first valid key (by request order) wins; the rest are
    reported as dropped even though they were individually valid."""
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter(
        {"main_objection": "price", "sale_result": "Sale"}, allowlist
    )
    assert bedrock_filter == {"equals": {"key": "main_objection", "value": "price"}}
    assert applied == "main_objection"
    assert dropped == ["sale_result"]


def test_first_invalid_key_falls_through_to_next_valid_one():
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter(
        {"agent_performance_score": 5, "main_objection": "price"}, allowlist
    )
    assert bedrock_filter == {"equals": {"key": "main_objection", "value": "price"}}
    assert applied == "main_objection"
    assert dropped == ["agent_performance_score"]


def test_all_invalid_keys_returns_none_with_all_dropped():
    allowlist = load_filter_allowlist()
    bedrock_filter, applied, dropped = build_filter(
        {"agent_performance_score": 5, "not_a_field": "x"}, allowlist
    )
    assert bedrock_filter is None
    assert applied is None
    assert set(dropped) == {"agent_performance_score", "not_a_field"}


def test_filter_builder_is_deterministic():
    allowlist = load_filter_allowlist()
    result1 = build_filter({"main_objection": "price", "sale_result": "Sale"}, allowlist)
    result2 = build_filter({"main_objection": "price", "sale_result": "Sale"}, allowlist)
    assert result1 == result2
