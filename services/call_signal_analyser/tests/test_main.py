from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_TRANSCRIPT = "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing."

CANONICAL_PAYLOAD = {
    "transcript": VALID_TRANSCRIPT,
    "audio_features": {
        "call_duration_seconds": 420,
        "silence_ratio": 0.18,
        "speaking_rate_wpm": 145,
        "speech_to_non_speech_ratio": 0.82,
        "agent_talk_ratio": 0.62,
        "average_energy_level": "medium",
    },
    "structured_fields": {
        "customer_intent": "high",
        "main_objection": "price",
        "customer_sentiment": "mixed",
        "closing_attempt": "weak",
        "decision_maker_present": True,
    },
}


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "call_signal_analyser", "version": "0.1.0"}


def test_analyse_call_matches_documented_example():
    """The exact example from CLAUDE.md / docs/api_contracts.md — pins the
    documented mock rules to a known, reviewable output."""
    resp = client.post("/analyse-call", json=CANONICAL_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["predicted_outcome"] == "Follow-up Needed"
    assert body["lead_quality_score"] == 4
    assert body["agent_performance_score"] == 3
    assert body["risk_level"] == "Medium"
    assert body["confidence"] == 0.72
    assert body["detected_signals"] == ["price objection", "high customer interest", "weak closing attempt"]
    assert body["human_review_required"] is False
    assert body["mock"] is True


def test_analyse_call_is_deterministic():
    resp1 = client.post("/analyse-call", json=CANONICAL_PAYLOAD)
    resp2 = client.post("/analyse-call", json=CANONICAL_PAYLOAD)
    assert resp1.json() == resp2.json()


def test_low_confidence_triggers_human_review():
    payload = {
        **CANONICAL_PAYLOAD,
        "structured_fields": {
            "customer_intent": "unclear",
            "main_objection": "none",
            "customer_sentiment": "negative",
            "closing_attempt": "none",
            "decision_maker_present": False,
        },
    }
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["confidence"] < 0.65
    assert body["human_review_required"] is True
    assert "none objection" not in body["detected_signals"]  # "none" is not a real objection signal


def test_high_intent_strong_closing_predicts_sale():
    payload = {
        **CANONICAL_PAYLOAD,
        "structured_fields": {
            "customer_intent": "high",
            "main_objection": "price",
            "customer_sentiment": "positive",
            "closing_attempt": "strong",
            "decision_maker_present": True,
        },
    }
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 200
    assert resp.json()["predicted_outcome"] == "Sale"


def test_low_intent_predicts_no_sale():
    payload = {
        **CANONICAL_PAYLOAD,
        "structured_fields": {
            "customer_intent": "low",
            "main_objection": "no_need",
            "customer_sentiment": "negative",
            "closing_attempt": "strong",
            "decision_maker_present": True,
        },
    }
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 200
    assert resp.json()["predicted_outcome"] == "No Sale"


def test_rejects_invalid_customer_intent_enum():
    payload = {**CANONICAL_PAYLOAD}
    payload["structured_fields"] = {**payload["structured_fields"], "customer_intent": "extremely_high"}
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_rejects_out_of_range_silence_ratio():
    payload = {**CANONICAL_PAYLOAD}
    payload["audio_features"] = {**payload["audio_features"], "silence_ratio": 0.9}
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 422


def test_rejects_out_of_range_call_duration():
    payload = {**CANONICAL_PAYLOAD}
    payload["audio_features"] = {**payload["audio_features"], "call_duration_seconds": 10}
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 422


def test_rejects_missing_structured_fields():
    resp = client.post("/analyse-call", json={"transcript": VALID_TRANSCRIPT, "audio_features": CANONICAL_PAYLOAD["audio_features"]})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_rejects_short_transcript():
    payload = {**CANONICAL_PAYLOAD, "transcript": "too short"}
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 422
