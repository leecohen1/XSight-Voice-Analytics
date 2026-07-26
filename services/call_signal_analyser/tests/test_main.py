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
    documented mock rules to a known, reviewable output. Fixed regression
    check: fully-populated audio_features must still reproduce this exactly
    after the demo-day missing-evidence changes (zero missing features means
    zero confidence penalty)."""
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
    assert body["missing_features"] == []


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


# --- Missing audio evidence (demo-day uncertainty pass) ---------------------
#
# Ground Truth Rule: a feature that can't be measured must be reported
# missing, never fabricated/defaulted (e.g. never a silently-defaulted
# silence_ratio: 0.0). These tests confirm: (1) omitted/null audio_features
# fields never trigger a 422, (2) they are reported verbatim in
# `missing_features`, (3) each missing feature lowers confidence by the
# documented per-feature penalty, and (4) a missing *critical* feature
# (silence_ratio or agent_talk_ratio) forces human_review_required even when
# the resulting confidence number alone would stay >= 0.65.

def test_some_noncritical_audio_features_missing_lowers_confidence():
    """Omitting a non-critical audio feature (call_duration_seconds) must
    still return 200, report it as missing, apply the standard -0.05
    penalty, and NOT force human review on its own (confidence stays >= 0.65
    and no critical feature is missing)."""
    payload = {
        **CANONICAL_PAYLOAD,
        "audio_features": {
            **CANONICAL_PAYLOAD["audio_features"],
            "call_duration_seconds": None,
        },
    }
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["missing_features"] == ["call_duration_seconds"]
    assert body["confidence"] == 0.67  # 0.72 documented baseline - 0.05 standard penalty
    assert body["human_review_required"] is False


def test_missing_critical_audio_feature_forces_human_review():
    """Even with structured fields strong enough to keep the confidence
    formula itself at 0.75 (>= 0.65 threshold), a missing critical feature
    (agent_talk_ratio) must force human_review_required to True — incomplete
    load-bearing evidence is not the same guarantee as complete evidence at
    the same confidence number."""
    payload = {
        **CANONICAL_PAYLOAD,
        "audio_features": {
            **CANONICAL_PAYLOAD["audio_features"],
            "agent_talk_ratio": None,
        },
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
    body = resp.json()
    assert body["missing_features"] == ["agent_talk_ratio"]
    assert body["confidence"] == 0.75
    assert body["human_review_required"] is True


def test_all_audio_features_missing_never_fabricated():
    """With every scored audio feature omitted, the service must still
    return 200 (never 422 for a missing-but-optional field), report all five
    as missing (never defaulting any to 0.0 or another fabricated number),
    apply the full stacked penalty, and require human review."""
    payload = {
        **CANONICAL_PAYLOAD,
        "audio_features": {"average_energy_level": "medium"},
    }
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["missing_features"] == [
        "call_duration_seconds",
        "silence_ratio",
        "speaking_rate_wpm",
        "speech_to_non_speech_ratio",
        "agent_talk_ratio",
    ]
    assert body["confidence"] == 0.27
    assert body["human_review_required"] is True
    assert body["risk_level"] == "High"


def test_missing_audio_features_via_omission_not_just_explicit_null():
    """Fields left out of the JSON body entirely (not just explicit `null`)
    must behave identically to explicit null — both mean 'unmeasured'."""
    payload = {**CANONICAL_PAYLOAD, "audio_features": {}}
    resp = client.post("/analyse-call", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["missing_features"]) == {
        "call_duration_seconds",
        "silence_ratio",
        "speaking_rate_wpm",
        "speech_to_non_speech_ratio",
        "agent_talk_ratio",
    }
