"""Deterministic mock scoring rules for the Call Signal Analyser (Phase 6).

These rules exist ONLY to produce a repeatable, testable mock response with
the correct shape and value ranges. They are not a trained model and must
not be treated as predictive logic — real inference is a PyTorch classifier
trained in Phase 13 (see docs/dataset_design.md §15-§17).

All tables below are the complete, documented rule set — nothing here is
hidden or randomized, so the same input always produces the same output.
"""
from app.models import AnalyseCallRequest, AnalyseCallResponse

_CONFIDENCE_BASE = 0.70

_INTENT_CONFIDENCE_ADJ = {"high": 0.10, "medium": 0.0, "low": -0.15, "unclear": -0.25}
_CLOSING_CONFIDENCE_ADJ = {"strong": 0.05, "medium": 0.02, "weak": -0.05, "none": -0.15}
_SENTIMENT_CONFIDENCE_ADJ = {"positive": 0.05, "neutral": 0.0, "mixed": -0.03, "negative": -0.10}
_DECISION_MAKER_CONFIDENCE_ADJ = {True: 0.0, False: -0.08}

_LEAD_QUALITY_BY_INTENT = {"high": 4, "medium": 3, "low": 2, "unclear": 1}
_AGENT_PERFORMANCE_BY_CLOSING = {"strong": 5, "medium": 4, "weak": 3, "none": 1}

_INTEREST_LABEL_BY_INTENT = {
    "high": "high customer interest",
    "medium": "moderate customer interest",
    "low": "low customer interest",
    "unclear": "unclear customer interest",
}

HUMAN_REVIEW_CONFIDENCE_THRESHOLD = 0.65


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_confidence(fields) -> float:
    raw = (
        _CONFIDENCE_BASE
        + _INTENT_CONFIDENCE_ADJ[fields.customer_intent]
        + _CLOSING_CONFIDENCE_ADJ[fields.closing_attempt]
        + _SENTIMENT_CONFIDENCE_ADJ[fields.customer_sentiment]
        + _DECISION_MAKER_CONFIDENCE_ADJ[fields.decision_maker_present]
    )
    return round(_clamp(raw, 0.0, 1.0), 2)


def compute_predicted_outcome(fields) -> str:
    # Weak/no closing attempt always leaves the call open, regardless of
    # intent — mirrors Contrast Case 3 in the historical dataset (a
    # well-qualified call that stays "Follow-up Needed" due to weak closing).
    if fields.closing_attempt in ("weak", "none"):
        return "Follow-up Needed"
    if fields.customer_intent == "high" and fields.closing_attempt in ("strong", "medium"):
        return "Sale"
    if fields.customer_intent == "low":
        return "No Sale"
    return "Follow-up Needed"


def compute_risk_level(confidence: float) -> str:
    if confidence >= 0.75:
        return "Low"
    if confidence >= 0.50:
        return "Medium"
    return "High"


def compute_detected_signals(fields) -> list[str]:
    signals = []
    if fields.main_objection != "none":
        signals.append(f"{fields.main_objection} objection")
    signals.append(_INTEREST_LABEL_BY_INTENT[fields.customer_intent])
    signals.append(f"{fields.closing_attempt} closing attempt")
    if not fields.decision_maker_present:
        signals.append("decision-maker not present")
    return signals


def analyse(request: AnalyseCallRequest) -> AnalyseCallResponse:
    fields = request.structured_fields

    confidence = compute_confidence(fields)
    human_review_required = confidence < HUMAN_REVIEW_CONFIDENCE_THRESHOLD

    return AnalyseCallResponse(
        predicted_outcome=compute_predicted_outcome(fields),
        lead_quality_score=_LEAD_QUALITY_BY_INTENT[fields.customer_intent],
        agent_performance_score=_AGENT_PERFORMANCE_BY_CLOSING[fields.closing_attempt],
        risk_level=compute_risk_level(confidence),
        confidence=confidence,
        detected_signals=compute_detected_signals(fields),
        human_review_required=human_review_required,
        mock=True,
    )
