"""Unit tests for app/metadata_safety.py — ensures metadata_json can never
become an unrestricted dump of call content."""
from app.metadata_safety import sanitize_metadata


def test_allowed_keys_pass_through():
    sanitized, stripped = sanitize_metadata({"filter_applied": True, "results_returned": 3})
    assert sanitized == {"filter_applied": True, "results_returned": 3}
    assert stripped == []


def test_disallowed_key_is_stripped_not_rejected():
    sanitized, stripped = sanitize_metadata({"filter_applied": True, "customer_notes": "call me back"})
    assert sanitized == {"filter_applied": True}
    assert "customer_notes" in stripped


def test_transcript_like_key_never_stored():
    sanitized, stripped = sanitize_metadata({"transcript": "Agent: hi... Customer: ...", "prompt": "system prompt text"})
    assert sanitized == {}
    assert set(stripped) == {"transcript", "prompt"}


def test_oversized_string_value_stripped():
    sanitized, stripped = sanitize_metadata({"search_type": "x" * 500})
    assert "search_type" not in sanitized
    assert "search_type" in stripped


def test_non_dict_input_returns_empty():
    sanitized, stripped = sanitize_metadata("not a dict")
    assert sanitized == {}
    assert stripped == []


def test_none_input_returns_empty():
    sanitized, stripped = sanitize_metadata(None)
    assert sanitized == {}
    assert stripped == []


def test_nested_object_value_stripped():
    sanitized, stripped = sanitize_metadata({"clamped_fields": {"nested": "object"}})
    assert "clamped_fields" not in sanitized
    assert "clamped_fields" in stripped


def test_safe_list_of_scalars_allowed():
    sanitized, stripped = sanitize_metadata({"dropped_filter_keys": ["a", "b", "c"]})
    assert sanitized == {"dropped_filter_keys": ["a", "b", "c"]}
    assert stripped == []


def test_oversized_list_stripped():
    sanitized, stripped = sanitize_metadata({"dropped_filter_keys": [str(i) for i in range(50)]})
    assert "dropped_filter_keys" not in sanitized
    assert "dropped_filter_keys" in stripped
