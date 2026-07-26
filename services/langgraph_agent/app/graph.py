"""Real LangGraph implementation of the planned reasoning pipeline (Phase 14
partial: StateGraph wiring today; LLM backend for the Planner/Synthesizer
nodes is still TBD).

Graph shape, matching the architecture doc (CLAUDE.md, component 6):

    START -> Planner -> Evidence Reconciliation -> Synthesizer -> END

- Planner Node: determines which evidence sources are actually present and
  worth reasoning over for this call.
- Evidence Reconciliation Node: compares the transcript, structured
  extraction, RAG results, and Call Signal Analyser results; detects
  conflicts, missing evidence, and inconsistencies. (In this implementation,
  the generic "Tool Execution" step is adapted into Evidence Reconciliation
  because n8n performs the external HTTP tool calls before this service is
  invoked — see CLAUDE.md, component 6.)
- Synthesizer Node: produces `reasoning_steps`, `evidence_conflicts`,
  `coaching_points`, and `recommended_next_action`.

This module builds and compiles an actual `langgraph.graph.StateGraph` and
invokes it per-request — this is a genuinely executing LangGraph graph, not
a renamed function chain. Per the current, explicit scope decision, the
per-node logic is still deterministic and rule-based: no LLM call is made
anywhere in this graph, and this service makes no outbound HTTP calls of its
own (n8n fetches RAG/Signal-Analyser evidence and passes it in). Real LLM
reasoning inside these nodes remains TBD (Phase 14 LLM backend decision).
"""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.models import AgentRunRequest

LOW_CONFIDENCE_THRESHOLD = 0.65

DEFAULT_COACHING_POINT = "Confirm a concrete follow-up date."
WEAK_CLOSING_COACHING_POINT = "Strengthen the closing ask — propose a concrete next step with a date."


class GraphState(TypedDict, total=False):
    """State object threaded through the compiled StateGraph.

    Populated in two waves:
    1. Input fields, seeded from `AgentRunRequest` before the graph runs.
    2. Output fields, added incrementally by each node as it runs — LangGraph
       merges each node's returned dict into the shared state.
    """

    # --- Inputs (copied from the request) ---
    question: str
    transcript: str
    metadata: dict[str, Any]
    structured_extraction: dict[str, Any]
    rag_results: dict[str, Any]
    signal_analysis: dict[str, Any]
    # Not part of today's documented AgentRunRequest contract (see
    # docs/api_contracts.md §4), but the architecture doc (CLAUDE.md,
    # component 6) lists an `agent_enrichment` input for this service's
    # future n8n AI Agent Node integration. Modeled here so the state
    # schema doesn't need to change shape when that field is added
    # upstream — it simply defaults to `{}` until then.
    agent_enrichment: dict[str, Any]

    # --- Planner Node output ---
    plan: dict[str, bool]

    # --- Evidence Reconciliation Node output ---
    evidence_conflicts: list[str]
    evidence_used: list[str]

    # --- Synthesizer Node output ---
    answer: str
    reasoning_steps: list[str]
    coaching_points: list[str]
    recommended_next_action: str

    # --- Bookkeeping (for the optional `graph_trace` debug field) ---
    graph_trace: list[str]


def _record(state: GraphState, node_name: str) -> list[str]:
    """Appends `node_name` to a copy of the running trace of executed nodes."""
    trace = list(state.get("graph_trace", []))
    trace.append(node_name)
    return trace


def planner_node(state: GraphState) -> dict:
    """Determines which evidence sources are actually present and worth
    reasoning over for this call."""
    rag_results = state.get("rag_results", {})
    plan = {
        "has_structured_extraction": bool(state.get("structured_extraction")),
        "has_rag_results": bool(rag_results.get("similar_calls") or rag_results.get("citations")),
        "has_signal_analysis": bool(state.get("signal_analysis")),
    }
    return {"plan": plan, "graph_trace": _record(state, "Planner")}


def evidence_reconciliation_node(state: GraphState) -> dict:
    """Compares the available evidence sources and flags conflicts or gaps.

    Deterministic conflict rules (documented, not learned):
    1. Call Signal Analyser confidence below the human-review threshold
       (0.65) while other evidence exists — evidence is present but
       unreliable, so it's flagged rather than trusted silently.
    2. RAG results claim similarity/citations but signal_analysis predicts
       an outcome with High risk — surfaced as a conflict worth a human's
       attention, not resolved automatically.
    """
    plan = state["plan"]
    signal = state.get("signal_analysis", {})

    conflicts: list[str] = []
    evidence_used: list[str] = []

    if plan["has_structured_extraction"]:
        evidence_used.append("structured_extraction")
    if plan["has_rag_results"]:
        evidence_used.append("rag_service")
    if plan["has_signal_analysis"]:
        evidence_used.append("call_signal_analyser")

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

    return {
        "evidence_conflicts": conflicts,
        "evidence_used": evidence_used,
        "graph_trace": _record(state, "Evidence Reconciliation"),
    }


def synthesizer_node(state: GraphState) -> dict:
    """Produces the final reasoning output from the plan and reconciliation results."""
    plan = state["plan"]
    structured_extraction = state.get("structured_extraction", {})
    signal = state.get("signal_analysis", {})
    rag_results = state.get("rag_results", {})

    reasoning_steps: list[str] = []
    if plan["has_structured_extraction"]:
        reasoning_steps.append("Reviewed structured extraction")
    if plan["has_rag_results"]:
        reasoning_steps.append("Reviewed historical evidence")
    if plan["has_signal_analysis"]:
        reasoning_steps.append("Reviewed call signal output")
    reasoning_steps.append("Synthesized coaching recommendation")

    closing_attempt = structured_extraction.get("closing_attempt")
    coaching_points = (
        [WEAK_CLOSING_COACHING_POINT] if closing_attempt in ("weak", "none") else [DEFAULT_COACHING_POINT]
    )

    predicted_outcome = signal.get("predicted_outcome")
    if predicted_outcome == "Follow-up Needed":
        recommended_next_action = "Schedule a follow-up with the decision-maker."
    elif predicted_outcome == "No Sale":
        recommended_next_action = "Log lost-deal reasons and share with the sales manager for coaching."
    elif predicted_outcome == "Sale":
        recommended_next_action = "Confirm onboarding details and send the contract for signature."
    else:
        recommended_next_action = "Review the call summary with the sales manager."

    citations = rag_results.get("citations", [])
    citation_note = f" citing {', '.join(citations)}" if citations else ""
    answer = (
        f"Reasoning answer based on the supplied evidence{citation_note}. "
        f"Reasoning is deterministic/rule-based — no LLM call is made yet (Phase 14 LLM backend decision pending)."
    )

    return {
        "answer": answer,
        "reasoning_steps": reasoning_steps,
        "coaching_points": coaching_points,
        "recommended_next_action": recommended_next_action,
        "graph_trace": _record(state, "Synthesizer"),
    }


def build_graph():
    """Builds and compiles the LangGraph StateGraph: START -> Planner ->
    Evidence Reconciliation -> Synthesizer -> END."""
    graph = StateGraph(GraphState)

    graph.add_node("planner", planner_node)
    graph.add_node("evidence_reconciliation", evidence_reconciliation_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "evidence_reconciliation")
    graph.add_edge("evidence_reconciliation", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# Compiled once at import time and reused across requests. The graph itself
# holds no per-request state — each `invoke()` call gets a fresh state dict —
# so a single compiled graph instance is safe to share across requests. No
# checkpointer is configured, so LangGraph does not persist state between
# requests or across process restarts (single-turn only — see README
# "Limitations").
COMPILED_GRAPH = build_graph()


def run_graph(request: AgentRunRequest) -> dict:
    """Builds the initial state from the request, invokes the compiled
    StateGraph, and shapes the final state into the documented response
    dict."""
    initial_state: GraphState = {
        "question": request.question,
        "transcript": request.transcript,
        "metadata": request.metadata,
        "structured_extraction": request.structured_extraction,
        "rag_results": request.rag_results.model_dump(),
        "signal_analysis": request.signal_analysis,
        "agent_enrichment": getattr(request, "agent_enrichment", None) or {},
        "graph_trace": [],
    }

    final_state = COMPILED_GRAPH.invoke(initial_state)

    return {
        "answer": final_state["answer"],
        "reasoning_steps": final_state["reasoning_steps"],
        "evidence_conflicts": final_state["evidence_conflicts"],
        "coaching_points": final_state["coaching_points"],
        "recommended_next_action": final_state["recommended_next_action"],
        "evidence_used": final_state["evidence_used"],
        # `mock` retains its established meaning from the Phase 6 skeleton:
        # true = no LLM call was made, reasoning is deterministic/rule-based.
        # That meaning is UNCHANGED and still accurate today — this graph
        # runs for real (see `graph_trace` below for proof), but no node
        # calls an LLM yet. See README "Limitations" for the full picture.
        "mock": True,
        # New, additive field: the actual sequence of LangGraph node names
        # that executed for this request, in order. Proves this is a real
        # StateGraph.invoke() run, not a renamed function chain.
        "graph_trace": final_state["graph_trace"],
    }
