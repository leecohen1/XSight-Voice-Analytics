"""Deterministic mock scoring rules for the Call Signal Analyser (Phase 6).

These rules exist ONLY to produce a repeatable, testable mock response with
the correct shape and value ranges. They are not a trained model and must
not be treated as predictive logic — real inference is a PyTorch classifier
trained in Phase 13 (see docs/dataset_design.md §15-§17).

All tables below are the complete, documented rule set — nothing here is
hidden or randomized, so the same input always produces the same output.

Demo-day uncertainty pass (see CLAUDE.md Ground Truth Rules): audio-derived
features that couldn't be measured arrive as `None` (app/models.py) rather
than a fabricated default. This module never substitutes a fabricated number
for a missing audio feature — instead, missing audio evidence is (a) detected,
(b) turned into an explicit confidence penalty, (c) surfaced in the response
as `missing_features`, and (d) allowed to force `human_review_required` even
when the confidence formula alone wouldn't have crossed the threshold.
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

# --- Missing audio evidence -------------------------------------------------
#
# The five scored AudioFeatures fields (average_energy_level is excluded: it
# was already optional pre-demo-day and is not used in scoring). Order here
# is also the order features are reported in `missing_features`.
_AUDIO_FEATURE_FIELDS = (
    "call_duration_seconds",
    "silence_ratio",
    "speaking_rate_wpm",
    "speech_to_non_speech_ratio",
    "agent_talk_ratio",
)

# "Critical" features are the ones the rest of the pipeline leans on most
# heavily downstream of this service: `agent_talk_ratio` is the direct input
# to the talk-time coaching signal (and the only speaker-tagging-derived
# feature at all), and `silence_ratio` is the primary engagement/dead-air
# signal used to sanity-check the transcript-derived intent/closing read.
# Losing either one means the confidence score is missing a load-bearing
# input, not just a nice-to-have one — so a missing critical feature forces
# human review regardless of what the rest of the formula computes.
# `call_duration_seconds`, `speaking_rate_wpm`, and
# `speech_to_non_speech_ratio` are still real evidence (hence still penalized)
# but are corroborating/contextual rather than load-bearing on their own.
_CRITICAL_AUDIO_FEATURES = frozenset({"silence_ratio", "agent_talk_ratio"})

# Confidence penalty applied PER missing feature, by criticality. Applied on
# top of the existing structured-fields adjustments, before clamping/rounding.
_MISSING_FEATURE_CONFIDENCE_ADJ = {"critical": -0.15, "standard": -0.05}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def detect_missing_audio_features(audio_features) -> list[str]:
    """Return the names of AudioFeatures fields that are `None` (unmeasured),
    in `_AUDIO_FEATURE_FIELDS` order. Never treats a missing value as 0.0/a
    default — a field is either present with a validated value, or reported
    here as missing."""
    return [name for name in _AUDIO_FEATURE_FIELDS if getattr(audio_features, name) is None]


def compute_missing_feature_penalty(missing_features: list[str]) -> float:
    return sum(
        _MISSING_FEATURE_CONFIDENCE_ADJ["critical" if name in _CRITICAL_AUDIO_FEATURES else "standard"]
        for name in missing_features
    )


def compute_confidence(fields, missing_features: list[str]) -> float:
    raw = (
        _CONFIDENCE_BASE
        + _INTENT_CONFIDENCE_ADJ[fields.customer_intent]
        + _CLOSING_CONFIDENCE_ADJ[fields.closing_attempt]
        + _SENTIMENT_CONFIDENCE_ADJ[fields.customer_sentiment]
        + _DECISION_MAKER_CONFIDENCE_ADJ[fields.decision_maker_present]
        + compute_missing_feature_penalty(missing_features)
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

    missing_features = detect_missing_audio_features(request.audio_features)
    confidence = compute_confidence(fields, missing_features)

    # Missing critical audio evidence forces human review even if the
    # confidence formula alone stays >= threshold — an incomplete-evidence
    # score is not the same guarantee as a complete-evidence score at the
    # same number, so it must not silently pass as if it were.
    has_missing_critical_feature = any(name in _CRITICAL_AUDIO_FEATURES for name in missing_features)
    human_review_required = confidence < HUMAN_REVIEW_CONFIDENCE_THRESHOLD or has_missing_critical_feature

    return AnalyseCallResponse(
        predicted_outcome=compute_predicted_outcome(fields),
        lead_quality_score=_LEAD_QUALITY_BY_INTENT[fields.customer_intent],
        agent_performance_score=_AGENT_PERFORMANCE_BY_CLOSING[fields.closing_attempt],
        risk_level=compute_risk_level(confidence),
        confidence=confidence,
        detected_signals=compute_detected_signals(fields),
        human_review_required=human_review_required,
        mock=True,
        missing_features=missing_features,
    )
