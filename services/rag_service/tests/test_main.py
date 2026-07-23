"""Endpoint-level tests for the real Amazon Bedrock Knowledge Base
integration. boto3 is always mocked (patched at app.bedrock_client._client)
— no live AWS access is required or used by this suite. The one live check
against the real Knowledge Base is a separate, explicit smoke test run
outside pytest (see services/rag_service/README.md)."""
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_TRANSCRIPT = "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing."


def _bedrock_result(call_id, agent_name, sale_result, main_objection, score):
    return {
        "content": {"text": f"Call ID: {call_id}\n...", "type": "TEXT"},
        "location": {"s3Location": {"uri": f"s3://bucket/prefix/{call_id}.txt"}, "type": "S3"},
        "metadata": {
            "call_id": call_id, "agent_name": agent_name,
            "sale_result": sale_result, "main_objection": main_objection,
        },
        "score": score,
    }


def _mock_client(retrieve_return=None, retrieve_side_effect=None):
    mock = MagicMock()
    if retrieve_side_effect is not None:
        mock.retrieve.side_effect = retrieve_side_effect
    else:
        mock.retrieve.return_value = retrieve_return or {"retrievalResults": []}
    return mock


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "service": "rag_service", "version": "0.2.0"}


# ---------------------------------------------------------------
# Valid semantic retrieval
# ---------------------------------------------------------------

def test_query_success_semantic_retrieval():
    mock = _mock_client(retrieve_return={"retrievalResults": [
        _bedrock_result("CALL_007", "Daniel Cohen", "Sale", "price", 0.85),
        _bedrock_result("CALL_015", "Michael Ben-David", "No Sale", "price", 0.72),
    ]})
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT, "top_k": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["similar_calls"]) == 2
    assert body["citations"] == ["CALL_007", "CALL_015"]
    assert body["grounded"] is True
    assert body["retrieval_metadata"]["filter_applied"] is False
    assert body["retrieval_metadata"]["search_type"] == "SEMANTIC"

    call_kwargs = mock.retrieve.call_args.kwargs
    assert call_kwargs["knowledgeBaseId"] == "TESTKBID123"
    assert call_kwargs["retrievalQuery"] == {"text": VALID_TRANSCRIPT}
    vector_config = call_kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]
    assert vector_config["numberOfResults"] == 2
    assert vector_config["overrideSearchType"] == "SEMANTIC"
    assert "filter" not in vector_config


# ---------------------------------------------------------------
# Metadata filtering
# ---------------------------------------------------------------

def test_query_with_allowed_filter_is_passed_to_bedrock():
    mock = _mock_client(retrieve_return={"retrievalResults": [
        _bedrock_result("CALL_007", "Daniel Cohen", "Sale", "price", 0.85),
    ]})
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={
            "transcript": VALID_TRANSCRIPT, "filters": {"main_objection": "price"},
        })
    assert resp.status_code == 200
    body = resp.json()
    assert body["retrieval_metadata"]["filter_requested"] == "main_objection"
    assert body["retrieval_metadata"]["filter_applied"] is True

    vector_config = mock.retrieve.call_args.kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]
    assert vector_config["filter"] == {"equals": {"key": "main_objection", "value": "price"}}


def test_query_with_unsupported_filter_key_is_dropped_not_rejected():
    mock = _mock_client(retrieve_return={"retrievalResults": [
        _bedrock_result("CALL_007", "Daniel Cohen", "Sale", "price", 0.85),
    ]})
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={
            "transcript": VALID_TRANSCRIPT, "filters": {"agent_performance_score": 5},
        })
    assert resp.status_code == 200  # not rejected — request still succeeds
    body = resp.json()
    assert body["retrieval_metadata"]["filter_applied"] is False
    assert body["retrieval_metadata"]["dropped_filter_keys"] == ["agent_performance_score"]

    vector_config = mock.retrieve.call_args.kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]
    assert "filter" not in vector_config


def test_query_filter_retried_unfiltered_when_zero_results():
    """Small-Corpus Filter Policy: retry without filters if a filtered
    query returns too few (here: zero) results."""
    mock = MagicMock()
    mock.retrieve.side_effect = [
        {"retrievalResults": []},  # first call, filtered
        {"retrievalResults": [_bedrock_result("CALL_009", "X", "No Sale", "price", 0.6)]},  # retry, unfiltered
    ]
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={
            "transcript": VALID_TRANSCRIPT, "filters": {"main_objection": "price"},
        })
    assert resp.status_code == 200
    body = resp.json()
    assert mock.retrieve.call_count == 2
    first_call_config = mock.retrieve.call_args_list[0].kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]
    second_call_config = mock.retrieve.call_args_list[1].kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]
    assert "filter" in first_call_config
    assert "filter" not in second_call_config
    assert body["retrieval_metadata"]["filter_requested"] == "main_objection"
    assert body["retrieval_metadata"]["filter_applied"] is False  # the retry succeeded unfiltered
    assert body["citations"] == ["CALL_009"]


# ---------------------------------------------------------------
# Empty / malformed results — never fabricated
# ---------------------------------------------------------------

def test_query_empty_results_returns_not_enough_evidence():
    mock = _mock_client(retrieve_return={"retrievalResults": []})
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["similar_calls"] == []
    assert body["citations"] == []
    assert body["grounded"] is False
    assert body["insight"] == "Not enough evidence to identify similar historical calls for this transcript."


def test_query_malformed_bedrock_result_is_dropped_not_fabricated():
    malformed_and_good = [
        {  # missing call_id and main_objection
            "content": {"text": "...", "type": "TEXT"},
            "location": {"s3Location": {"uri": "s3://bucket/prefix/CALL_X.txt"}, "type": "S3"},
            "metadata": {"agent_name": "Someone", "sale_result": "Sale"},
            "score": 0.9,
        },
        _bedrock_result("CALL_007", "Daniel Cohen", "Sale", "price", 0.85),
    ]
    mock = _mock_client(retrieve_return={"retrievalResults": malformed_and_good})
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 200
    body = resp.json()
    # only the well-formed result survives — nothing invented for the malformed one
    assert body["citations"] == ["CALL_007"]
    assert len(body["similar_calls"]) == 1


# ---------------------------------------------------------------
# Bedrock error mapping
# ---------------------------------------------------------------

def _client_error(code, message="error"):
    return ClientError({"Error": {"Code": code, "Message": message}}, "Retrieve")


def test_query_bedrock_access_denied_returns_502():
    mock = _mock_client(retrieve_side_effect=_client_error("AccessDeniedException"))
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "UPSTREAM_ACCESS_DENIED"
    assert "AccessDenied" not in resp.text or "Message" not in resp.json()["error"]  # no raw AWS detail leaked


def test_query_bedrock_validation_exception_returns_400():
    mock = _mock_client(retrieve_side_effect=_client_error("ValidationException"))
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "UPSTREAM_VALIDATION_ERROR"


def test_query_bedrock_throttling_returns_429():
    mock = _mock_client(retrieve_side_effect=_client_error("ThrottlingException"))
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "UPSTREAM_THROTTLED"


def test_query_bedrock_generic_service_error_returns_503():
    mock = _mock_client(retrieve_side_effect=_client_error("InternalServerException"))
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"


def test_query_network_error_returns_503():
    mock = _mock_client(retrieve_side_effect=EndpointConnectionError(endpoint_url="https://bedrock-agent-runtime.us-east-2.amazonaws.com"))
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"


def test_no_raw_aws_exception_text_in_any_error_response():
    mock = _mock_client(retrieve_side_effect=_client_error("AccessDeniedException", "arn:aws:iam::881490130721:role/secret-detail"))
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert "881490130721" not in resp.text
    assert "arn:aws" not in resp.text


# ---------------------------------------------------------------
# Missing configuration
# ---------------------------------------------------------------

def test_query_missing_required_env_returns_503(monkeypatch):
    monkeypatch.delenv("BEDROCK_KNOWLEDGE_BASE_ID", raising=False)
    resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "SERVICE_MISCONFIGURED"


def test_query_missing_region_returns_503(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "SERVICE_MISCONFIGURED"


# ---------------------------------------------------------------
# Request validation (unchanged contract)
# ---------------------------------------------------------------

def test_query_rejects_empty_transcript():
    resp = client.post("/query", json={"transcript": ""})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) >= 1


def test_query_rejects_too_short_transcript():
    resp = client.post("/query", json={"transcript": "too short"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_query_rejects_top_k_too_high():
    resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT, "top_k": 11})
    assert resp.status_code == 422


def test_query_rejects_top_k_too_low():
    resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT, "top_k": 0})
    assert resp.status_code == 422


def test_query_rejects_missing_transcript():
    resp = client.post("/query", json={})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_query_accepts_optional_current_call_metadata():
    """The `metadata` field (context about the *current* call, not a
    filter) remains accepted for backward compatibility with the documented
    request contract — it does not need to affect retrieval to be valid."""
    mock = _mock_client(retrieve_return={"retrievalResults": []})
    with patch("app.bedrock_client._client", return_value=mock):
        resp = client.post("/query", json={
            "transcript": VALID_TRANSCRIPT,
            "metadata": {"agent_name": "Sarah Levi", "call_duration_seconds": 300, "sale_result": "Sale"},
        })
    assert resp.status_code == 200


def test_404_uses_structured_error_shape():
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "HTTP_ERROR"
