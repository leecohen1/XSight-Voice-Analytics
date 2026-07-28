"""Deterministic attention + recovery-opportunity derivation.

Nothing in this module is model-generated. Every value is a pure function of
fields the pipeline (or the historical CSV) already established, so the same
inputs always produce the same priority score, and a reviewer can trace any
"why is this call flagged" question back to a rule rather than to a prompt.

This is the single implementation used by BOTH paths:
  * the historical seed script (app-side, over CSV-derived fields), and
  * live analyses (n8n posts the analysis; this service derives the blocks).

PRECEDENCE (first match wins, most severe first)
-------------------------------------------------
1. evidence_conflict        -- the pipeline's own evidence sources disagree
2. human_review             -- routing already demands a human, or a
                               follow-up was needed with nothing scheduled
3. critical_coaching        -- agent_performance_score <= 2
4. customer_dissatisfaction -- customer_sentiment == "negative"
5. recoverable_opportunity  -- lead_quality_score >= 4 and outcome != Sale
6. low_priority             -- nothing matched; attention.required = False

Rationale for this order: a call can easily match several rules at once (a
negative-sentiment call with a weak agent score and an unresolved
follow-up). Ranking by "who must act, and how urgently" -- system conflict,
then human-review obligation, then coaching, then customer risk, then
revenue upside -- keeps the single reported category the most actionable
one, instead of whichever rule happened to be evaluated first.

PRIORITY SCORE (0-100, integer)
--------------------------------
    score = category_base + modifiers, clamped to [0, 100]

    category_base:
        evidence_conflict         70
        human_review              60
        critical_coaching         55
        customer_dissatisfaction  45
        recoverable_opportunity   40
        low_priority               0

    modifiers (applied only when a category other than low_priority matched):
        lead_quality_score == 5                        +15
        lead_quality_score == 4                        +10
        agent_performance_score <= 2                   +10
        risk_level == "High"                           +10
        risk_level == "Medium"                          +5
        confidence is not None and confidence < 0.65    +8
        call_outcome == "Follow-up Needed"              +5

    Missing inputs contribute 0 -- a null confidence never scores as if it
    were low, and a null risk level never scores as if it were High.

PRIORITY BAND
-------------
    score >= 80  -> critical
    score >= 60  -> high
    score >= 35  -> medium
    otherwise    -> low
"""
from __future__ import annotations

from typing import Optional

from app.models import Attention, AttentionCategory, AttentionPriority, RecoveryOpportunity

CATEGORY_BASE_SCORE: dict[AttentionCategory, int] = {
    "evidence_conflict": 70,
    "human_review": 60,
    "critical_coaching": 55,
    "customer_dissatisfaction": 45,
    "recoverable_opportunity": 40,
    "low_priority": 0,
}

# Substrings that identify an evidence-conflict router reason. Matched
# case-insensitively against each router reason string, so both the n8n
# Router's machine codes ("langgraph_evidence_conflicts_detected") and a
# human-readable label ("Evidence conflict") are recognised.
EVIDENCE_CONFLICT_MARKERS = ("evidence_conflict", "evidence conflict")

# Router reason substrings that independently oblige a human review.
HUMAN_REVIEW_MARKERS = (
    "human_review",
    "human review",
    "confidence_below",
    "missing_historical_call_citations",
    "missing_citations",
    "not_parseable",
)

# Objection -> the concrete next offer. Every entry restates an action the
# objection itself implies; none introduces a price, discount, date, or
# commitment the source data never contained.
OFFER_BY_OBJECTION: dict[str, str] = {
    "price": "Prepare an itemized proposal separating platform cost from onboarding cost.",
    "timing": "Confirm quote validity in writing and book a dated check-in for the next budget cycle.",
    "trust": "Share security and compliance documentation, and offer a reference customer.",
    "competitor": "Prepare a side-by-side comparison covering the specific gap the customer named.",
    "authority": "Request a follow-up with the economic decision maker present.",
    "no_need": "Share a use-case brief tied to the specific pain the customer described.",
    "integration": "Book a technical scoping call to confirm the integration path.",
    "security": "Send the security packet and offer a review call with the security team.",
}
DEFAULT_OFFER = "Confirm the outstanding objection with the customer before proposing next steps."

FOLLOW_UP_WINDOW_BY_PRIORITY: dict[AttentionPriority, str] = {
    "critical": "within_24_hours",
    "high": "within_3_days",
    "medium": "within_1_week",
    "low": "within_2_weeks",
}


def _matches(reasons: list[str], markers: tuple[str, ...]) -> bool:
    lowered = [str(r).lower() for r in reasons or []]
    return any(marker in reason for reason in lowered for marker in markers)


def priority_band(score: int) -> AttentionPriority:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def derive_attention(
    *,
    call_outcome: Optional[str],
    customer_sentiment: Optional[str],
    agent_performance_score: Optional[int],
    lead_quality_score: Optional[int],
    risk_level: Optional[str],
    confidence: Optional[float],
    guardrail_status: Optional[str],
    router_reasons: Optional[list[str]] = None,
    follow_up_needed: Optional[bool] = None,
    next_meeting_scheduled: Optional[bool] = None,
) -> Attention:
    """Apply the documented precedence order and score formula."""
    reasons = list(router_reasons or [])

    category: AttentionCategory
    reason_text: str

    unresolved_follow_up = bool(follow_up_needed) and next_meeting_scheduled is False

    if _matches(reasons, EVIDENCE_CONFLICT_MARKERS):
        category = "evidence_conflict"
        reason_text = "The pipeline's evidence sources disagree on this call; a human must reconcile them."
    elif guardrail_status == "human_review_required" or _matches(reasons, HUMAN_REVIEW_MARKERS):
        category = "human_review"
        reason_text = "Routing sent this call to human review before the result can be trusted."
    elif unresolved_follow_up:
        category = "human_review"
        reason_text = "A follow-up was needed but no next meeting was scheduled."
    elif agent_performance_score is not None and agent_performance_score <= 2:
        category = "critical_coaching"
        reason_text = (
            f"Agent performance scored {agent_performance_score}/5 on this call; coaching is warranted."
        )
    elif customer_sentiment == "negative":
        category = "customer_dissatisfaction"
        reason_text = "Customer sentiment on this call was negative."
    elif lead_quality_score is not None and lead_quality_score >= 4 and call_outcome != "Sale":
        category = "recoverable_opportunity"
        reason_text = (
            f"Lead quality scored {lead_quality_score}/5 but the call did not close; "
            f"the opportunity looks recoverable."
        )
    else:
        return Attention(
            required=False, priority="low", priority_score=0, category="low_priority", reason=None
        )

    score = CATEGORY_BASE_SCORE[category]
    if lead_quality_score == 5:
        score += 15
    elif lead_quality_score == 4:
        score += 10
    if agent_performance_score is not None and agent_performance_score <= 2:
        score += 10
    if risk_level == "High":
        score += 10
    elif risk_level == "Medium":
        score += 5
    if confidence is not None and confidence < 0.65:
        score += 8
    if call_outcome == "Follow-up Needed":
        score += 5

    score = max(0, min(100, score))
    return Attention(
        required=True,
        priority=priority_band(score),
        priority_score=score,
        category=category,
        reason=reason_text,
    )


def derive_recovery_opportunity(
    *,
    call_outcome: Optional[str],
    lead_quality_score: Optional[int],
    main_objection: Optional[str],
    confidence: Optional[float],
    attention: Attention,
) -> RecoveryOpportunity:
    """A recoverable opportunity is a high-quality lead that did not close.

    `confidence` is passed through from the analysis when one was measured
    and stays None otherwise -- the historical corpus never produced a
    confidence, and inventing one here would violate the Ground Truth Rules.
    """
    detected = (
        lead_quality_score is not None
        and lead_quality_score >= 4
        and call_outcome is not None
        and call_outcome != "Sale"
    )
    if not detected:
        return RecoveryOpportunity(detected=False)

    objection_key = (main_objection or "").strip().lower()
    offer = OFFER_BY_OBJECTION.get(objection_key, DEFAULT_OFFER)
    objection_phrase = objection_key if objection_key and objection_key != "none" else "no explicit objection"

    return RecoveryOpportunity(
        detected=True,
        confidence=confidence,
        reason=(
            f"Lead quality {lead_quality_score}/5 with outcome '{call_outcome}' and "
            f"{objection_phrase} recorded as the main objection."
        ),
        recommended_offer=offer,
        recommended_follow_up_window=FOLLOW_UP_WINDOW_BY_PRIORITY[attention.priority],
    )
