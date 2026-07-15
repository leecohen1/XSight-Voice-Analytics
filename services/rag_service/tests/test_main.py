from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_TRANSCRIPT = "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing."


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "service": "rag_service", "version": "0.1.0"}


def test_query_success_default_top_k():
    resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mock"] is True
    assert body["grounded"] is True
    assert len(body["similar_calls"]) == 3  # default top_k
    assert body["citations"] == [c["call_id"] for c in body["similar_calls"]]
    assert all(0.0 <= c["similarity_score"] <= 1.0 for c in body["similar_calls"])


def test_query_success_respects_top_k():
    resp = client.post("/query", json={"transcript": VALID_TRANSCRIPT, "top_k": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["similar_calls"]) == 1
    assert len(body["citations"]) == 1


def test_query_is_deterministic():
    resp1 = client.post("/query", json={"transcript": VALID_TRANSCRIPT, "top_k": 2})
    resp2 = client.post("/query", json={"transcript": VALID_TRANSCRIPT, "top_k": 2})
    assert resp1.json()["similar_calls"] == resp2.json()["similar_calls"]


def test_query_with_metadata():
    resp = client.post(
        "/query",
        json={
            "transcript": VALID_TRANSCRIPT,
            "metadata": {"agent_name": "Sarah Levi", "call_duration_seconds": 300, "sale_result": "Sale"},
            "top_k": 2,
        },
    )
    assert resp.status_code == 200


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


def test_404_uses_structured_error_shape():
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "HTTP_ERROR"
