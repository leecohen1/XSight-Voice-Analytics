"""Unit tests for building QueryResponse from a raw Bedrock RetrievalOutcome
(app/response_builder.py) — the deterministic-mapping, citation-generation,
and no-fabrication requirements, isolated from HTTP/boto3 concerns."""
from app.bedrock_client import RetrievalOutcome
from app.response_builder import SIMILARITY_SCORE_FLOOR, build_response

GOOD_RESULT = {
    "content": {"text": "Call ID: CALL_001\n...", "type": "TEXT"},
    "location": {"s3Location": {"uri": "s3://bucket/prefix/CALL_001.txt"}, "type": "S3"},
    "metadata": {
        "call_id": "CALL_001", "agent_name": "Sarah Levi",
        "sale_result": "Sale", "main_objection": "price",
    },
    "score": 0.82,
}


def test_deterministic_similar_calls_mapping():
    outcome = RetrievalOutcome(results=[GOOD_RESULT], filter_applied=False, search_type="SEMANTIC")
    resp1 = build_response(outcome, "kb-1", None, [])
    resp2 = build_response(outcome, "kb-1", None, [])
    assert resp1 == resp2
    assert resp1.similar_calls[0].call_id == "CALL_001"
    assert resp1.similar_calls[0].agent_name == "Sarah Levi"
    assert resp1.similar_calls[0].sale_result == "Sale"
    assert resp1.similar_calls[0].main_objection == "price"
    assert resp1.similar_calls[0].similarity_score == 0.82


def test_citation_generation_matches_similar_calls():
    outcome = RetrievalOutcome(results=[GOOD_RESULT], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    assert resp.citations == [c.call_id for c in resp.similar_calls]
    assert resp.citations == ["CALL_001"]
    assert resp.grounded is True


def test_reason_text_is_built_only_from_retrieved_metadata():
    outcome = RetrievalOutcome(results=[GOOD_RESULT], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    reason = resp.similar_calls[0].reason
    assert "CALL_001" in reason
    assert "price" in reason
    assert "Sale" in reason


def test_empty_results_returns_not_enough_evidence():
    outcome = RetrievalOutcome(results=[], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    assert resp.similar_calls == []
    assert resp.citations == []
    assert resp.grounded is False
    assert resp.insight == "Not enough evidence to identify similar historical calls for this transcript."


def test_result_missing_required_metadata_is_dropped_not_fabricated():
    """A malformed Bedrock response (missing call_id, e.g.) must never be
    filled in with an invented value — it's dropped entirely."""
    malformed = {
        "content": {"text": "...", "type": "TEXT"},
        "location": {"s3Location": {"uri": "s3://bucket/prefix/CALL_002.txt"}, "type": "S3"},
        "metadata": {"agent_name": "Daniel Cohen", "sale_result": "Sale"},  # main_objection, call_id missing
        "score": 0.9,
    }
    outcome = RetrievalOutcome(results=[malformed], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    assert resp.similar_calls == []
    assert resp.citations == []
    assert resp.grounded is False


def test_result_missing_metadata_entirely_is_dropped():
    malformed = {
        "content": {"text": "...", "type": "TEXT"},
        "location": {"s3Location": {"uri": "s3://bucket/prefix/CALL_003.txt"}, "type": "S3"},
        "score": 0.9,
        # no "metadata" key at all
    }
    outcome = RetrievalOutcome(results=[malformed], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    assert resp.similar_calls == []


def test_result_missing_score_is_dropped():
    malformed = {
        "content": {"text": "...", "type": "TEXT"},
        "location": {"s3Location": {"uri": "s3://bucket/prefix/CALL_004.txt"}, "type": "S3"},
        "metadata": {"call_id": "CALL_004", "agent_name": "X", "sale_result": "Sale", "main_objection": "price"},
        # no "score"
    }
    outcome = RetrievalOutcome(results=[malformed], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    assert resp.similar_calls == []


def test_similarity_score_floor_excludes_weak_matches():
    weak_result = dict(GOOD_RESULT, score=SIMILARITY_SCORE_FLOOR - 0.01)
    outcome = RetrievalOutcome(results=[weak_result], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    assert resp.similar_calls == []
    assert resp.citations == []
    assert resp.grounded is False
    assert resp.retrieval_metadata.results_returned == 1
    assert resp.retrieval_metadata.results_above_threshold == 0


def test_similarity_score_at_floor_is_included():
    at_floor_result = dict(GOOD_RESULT, score=SIMILARITY_SCORE_FLOOR)
    outcome = RetrievalOutcome(results=[at_floor_result], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    assert len(resp.similar_calls) == 1


def test_retrieval_metadata_reports_filter_and_dropped_keys():
    outcome = RetrievalOutcome(results=[GOOD_RESULT], filter_applied=True, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-EDCC0WT0OB", "main_objection", ["agent_performance_score"])
    assert resp.retrieval_metadata.knowledge_base_id == "kb-EDCC0WT0OB"
    assert resp.retrieval_metadata.filter_requested == "main_objection"
    assert resp.retrieval_metadata.filter_applied is True
    assert resp.retrieval_metadata.dropped_filter_keys == ["agent_performance_score"]
    assert resp.retrieval_metadata.search_type == "SEMANTIC"


def test_multiple_results_preserve_bedrock_order_and_scores():
    second = dict(GOOD_RESULT, score=0.65,
                  metadata={**GOOD_RESULT["metadata"], "call_id": "CALL_005"})
    outcome = RetrievalOutcome(results=[GOOD_RESULT, second], filter_applied=False, search_type="SEMANTIC")
    resp = build_response(outcome, "kb-1", None, [])
    assert [c.call_id for c in resp.similar_calls] == ["CALL_001", "CALL_005"]
    assert [c.similarity_score for c in resp.similar_calls] == [0.82, 0.65]
