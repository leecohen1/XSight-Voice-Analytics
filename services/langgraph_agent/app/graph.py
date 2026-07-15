"""Deterministic mock of the planned LangGraph pipeline (Phase 6).

Planned internal graph (real implementation: Phase 14, LLM backend TBD):

    Planner Node -> Evidence Reconciliation Node -> Synthesizer Node

- Planner Node: determines which evidence and questions must be evaluated.
- Evidence Reconciliation Node: compares the transcript, structured
  extraction, RAG results, and Call Signal Analyser results; detects
  conflicts, missing evidence, and inconsistencies. (In this implementation,
  the generic "Tool Execution" step is adapted into Evidence Reconciliation
  because n8n performs the external HTTP tool calls before this service is
  invoked — see CLAUDE.md, component 6.)
- Synthesizer Node: produces `reasoning_steps`, `evidence_conflicts`,
  `coaching_points`, and `recommended_next_action`.

This module implements that three-step shape as plain, deterministic Python
functions chained together — NOT an installed/executed LangGraph graph. No
LLM call is made; every value below is rule-based so responses are
repeatable and testable. Real reasoning is Phase 14.
"""
from app.models import AgentRunRequest

LOW_CONFIDENCE_THRESHOLD = 0.65

DEFAULT_COACHING_POINT = "Confirm a concrete follow-up date."
WEAK_CLOSING_COACHING_POINT = "Strengthen the closing ask — propose a concrete next step with a date."


def planner_node(request: AgentRunRequest) -> dict:
    """Determines which evidence sources are actually present and worth
    reasoning over for this call."""
    plan = {
        "has_structured_extraction": bool(request.structured_extraction),
        "has_rag_results": bool(request.rag_results.similar_calls or request.rag_results.citations),
        "has_signal_analysis": bool(request.signal_analysis),
    }
    return plan


def evidence_reconciliation_node(request: AgentRunRequest, plan: dict) -> dict:
    """Compares the available evidence sources and flags conflicts or gaps.

    Deterministic conflict rules (documented, not learned):
    1. Call Signal Analyser confidence below the human-review threshold
       (0.65) while other evidence exists — evidence is present but
       unreliable, so it's flagged rather than trusted silently.
    2. RAG results claim similarity/citations but signal_analysis predicts
       an outcome with High risk — surfaced as a conflict worth a human's
       attention, not resolved automatically.
    """
    conflicts: list[str] = []
    evidence_used: list[str] = []

    if plan["has_structured_extraction"]:
        evidence_used.append("structured_extraction")
    if plan["has_rag_results"]:
        evidence_used.append("rag_service")
    if plan["has_signal_analysis"]:
        evidence_used.append("call_signal_analyser")

    signal = request.signal_analysis
    if plan["has_signal_analysis"]:
        confidence = signal.get("confidence")
        if isinstance(confidence, (int, float)) and confidence < LOW_CONFIDENCE_THRESHOLD:
            conflicts.append(
                f"Call Signal Analyser confidence ({confidence}) is below the "
                f"{LOW_CONFIDENCE_THRESHOLD} human-review threshold."
            )
        if plan["has_rag_results"] and signal.get("predicted_outcome") == "Sale" and signal.get("risk_level") == "High":
            conflicts.append(
                "Signal analyser predicts 'Sale' but simultaneously flags High risk — "
                "reconcile with RAG evidence before trusting either signal alone."
            )

    return {"conflicts": conflicts, "evidence_used": evidence_used}


def synthesizer_node(request: AgentRunRequest, plan: dict, reconciliation: dict) -> dict:
    """Produces the final reasoning output from the plan and reconciliation results."""
    reasoning_steps: list[str] = []
    if plan["has_structured_extraction"]:
        reasoning_steps.append("Reviewed structured extraction")
    if plan["has_rag_results"]:
        reasoning_steps.append("Reviewed historical evidence")
    if plan["has_signal_analysis"]:
        reasoning_steps.append("Reviewed call signal output")
    reasoning_steps.append("Synthesized coaching recommendation")

    closing_attempt = request.structured_extraction.get("closing_attempt")
    coaching_points = (
        [WEAK_CLOSING_COACHING_POINT] if closing_attempt in ("weak", "none") else [DEFAULT_COACHING_POINT]
    )

    predicted_outcome = request.signal_analysis.get("predicted_outcome")
    if predicted_outcome == "Follow-up Needed":
        recommended_next_action = "Schedule a follow-up with the decision-maker."
    elif predicted_outcome == "No Sale":
        recommended_next_action = "Log lost-deal reasons and share with the sales manager for coaching."
    elif predicted_outcome == "Sale":
        recommended_next_action = "Confirm onboarding details and send the contract for signature."
    else:
        recommended_next_action = "Review the call summary with the sales manager."

    citation_note = (
        f" citing {', '.join(request.rag_results.citations)}" if request.rag_results.citations else ""
    )
    answer = (
        f"Mock reasoning answer based on the supplied evidence{citation_note}. "
        f"Real reasoning is not implemented yet (Phase 14)."
    )

    return {
        "answer": answer,
        "reasoning_steps": reasoning_steps,
        "evidence_conflicts": reconciliation["conflicts"],
        "coaching_points": coaching_points,
        "recommended_next_action": recommended_next_action,
        "evidence_used": reconciliation["evidence_used"],
    }


def run_mock_graph(request: AgentRunRequest) -> dict:
    """Chains Planner -> Evidence Reconciliation -> Synthesizer, mirroring the
    planned LangGraph structure without installing/executing LangGraph itself."""
    plan = planner_node(request)
    reconciliation = evidence_reconciliation_node(request, plan)
    result = synthesizer_node(request, plan, reconciliation)
    result["mock"] = True
    return result
