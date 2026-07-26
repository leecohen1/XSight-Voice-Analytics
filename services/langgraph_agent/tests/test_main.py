from fastapi.testclient import TestClient

from app.graph import COMPILED_GRAPH, GraphState
from app.main import app

client = TestClient(app)

VALID_TRANSCRIPT = "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing."

FULL_PAYLOAD = {
    "question": "Why did this call fail and what should the agent improve?",
    "transcript": VALID_TRANSCRIPT,
    "metadata": {"agent_name": "Sarah Levi"},
    "structured_extraction": {"closing_attempt": "weak", "main_objection": "price"},
    "rag_results": {
        "similar_calls": [{"call_id": "CALL_007"}],
        "insight": "Similar price objection resolved via reframe.",
        "citations": ["CALL_007"],
    },
    "signal_analysis": {"predicted_outcome": "Follow-up Needed", "confidence": 0.72, "risk_level": "Medium"},
}


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "langgraph_agent", "version": "0.1.0"}


def test_agent_run_full_payload():
    resp = client.post("/agent/run", json=FULL_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["mock"] is True
    assert "CALL_007" in body["answer"]
    assert body["reasoning_steps"] == [
        "Reviewed structured extraction",
        "Reviewed historical evidence",
        "Reviewed call signal output",
        "Synthesized coaching recommendation",
    ]
    assert set(body["evidence_used"]) == {"structured_extraction", "rag_service", "call_signal_analyser"}
    assert body["coaching_points"] == ["Strengthen the closing ask — propose a concrete next step with a date."]
    assert body["recommended_next_action"] == "Schedule a follow-up with the decision-maker."
    assert body["evidence_conflicts"] == []
    # Proves the compiled StateGraph actually executed all three nodes, in
    # order, for this request — not just that the response shape matches.
    assert body["graph_trace"] == ["Planner", "Evidence Reconciliation", "Synthesizer"]


def test_compiled_graph_is_a_real_langgraph_stategraph():
    """Confirms app.graph builds and compiles an actual langgraph
    StateGraph (not a plain function chain) and that invoking it directly
    (bypassing the FastAPI layer entirely) runs all three named nodes and
    produces the expected output fields in the shared state."""
    from langgraph.graph.state import CompiledStateGraph

    assert isinstance(COMPILED_GRAPH, CompiledStateGraph)

    initial_state: GraphState = {
        "question": FULL_PAYLOAD["question"],
        "transcript": FULL_PAYLOAD["transcript"],
        "metadata": FULL_PAYLOAD["metadata"],
        "structured_extraction": FULL_PAYLOAD["structured_extraction"],
        "rag_results": FULL_PAYLOAD["rag_results"],
        "signal_analysis": FULL_PAYLOAD["signal_analysis"],
        "agent_enrichment": {},
        "graph_trace": [],
    }
    final_state = COMPILED_GRAPH.invoke(initial_state)

    assert final_state["graph_trace"] == ["Planner", "Evidence Reconciliation", "Synthesizer"]
    assert final_state["plan"] == {
        "has_structured_extraction": True,
        "has_rag_results": True,
        "has_signal_analysis": True,
    }
    assert "CALL_007" in final_state["answer"]
    assert final_state["evidence_conflicts"] == []


def test_agent_run_is_deterministic():
    resp1 = client.post("/agent/run", json=FULL_PAYLOAD)
    resp2 = client.post("/agent/run", json=FULL_PAYLOAD)
    assert resp1.json() == resp2.json()


def test_agent_run_minimal_payload_no_evidence():
    resp = client.post("/agent/run", json={"question": "What happened?", "transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reasoning_steps"] == ["Synthesized coaching recommendation"]
    assert body["evidence_used"] == []
    assert body["coaching_points"] == ["Confirm a concrete follow-up date."]
    assert body["recommended_next_action"] == "Review the call summary with the sales manager."
    # All three graph nodes still run even with no evidence supplied — the
    # graph's edges are fixed; only each node's output content varies.
    assert body["graph_trace"] == ["Planner", "Evidence Reconciliation", "Synthesizer"]


def test_agent_run_flags_low_confidence_conflict():
    payload = {**FULL_PAYLOAD, "signal_analysis": {"predicted_outcome": "Sale", "confidence": 0.4, "risk_level": "High"}}
    resp = client.post("/agent/run", json=payload)
    body = resp.json()
    assert any("confidence" in c for c in body["evidence_conflicts"])


def test_agent_run_flags_sale_vs_high_risk_conflict():
    payload = {**FULL_PAYLOAD, "signal_analysis": {"predicted_outcome": "Sale", "confidence": 0.8, "risk_level": "High"}}
    resp = client.post("/agent/run", json=payload)
    body = resp.json()
    assert any("High risk" in c for c in body["evidence_conflicts"])


def test_agent_run_strong_closing_uses_default_coaching_point():
    payload = {**FULL_PAYLOAD, "structured_extraction": {"closing_attempt": "strong"}}
    resp = client.post("/agent/run", json=payload)
    body = resp.json()
    assert body["coaching_points"] == ["Confirm a concrete follow-up date."]


def test_agent_run_rejects_missing_question():
    resp = client.post("/agent/run", json={"transcript": VALID_TRANSCRIPT})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_agent_run_rejects_short_transcript():
    payload = {**FULL_PAYLOAD, "transcript": "too short"}
    resp = client.post("/agent/run", json=payload)
    assert resp.status_code == 422


def test_agent_run_rejects_empty_question():
    payload = {**FULL_PAYLOAD, "question": "hi"[:1]}
    resp = client.post("/agent/run", json=payload)
    assert resp.status_code == 422


def test_404_uses_structured_error_shape():
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "HTTP_ERROR"
