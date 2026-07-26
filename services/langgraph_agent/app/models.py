"""Pydantic request/response models for the LangGraph Agent service.

A real LangGraph graph — Planner Node -> Evidence Reconciliation Node ->
Synthesizer Node, compiled as a `langgraph.graph.StateGraph` — reasons over
evidence n8n has already fetched (this service never calls the RAG Service
or Call Signal Analyser itself). See app/graph.py for the graph definition.
Per-node reasoning is still deterministic/rule-based; no LLM call is made
yet (Phase 14 LLM backend decision pending).
"""
from typing import Any

from pydantic import BaseModel, Field


class RagResults(BaseModel):
    similar_calls: list[dict[str, Any]] = Field(default_factory=list)
    insight: str = ""
    citations: list[str] = Field(default_factory=list)


class AgentRunRequest(BaseModel):
    question: str = Field(..., min_length=5)
    transcript: str = Field(..., min_length=20)
    metadata: dict[str, Any] = Field(default_factory=dict)
    structured_extraction: dict[str, Any] = Field(default_factory=dict)
    rag_results: RagResults = Field(default_factory=RagResults)
    signal_analysis: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    answer: str
    reasoning_steps: list[str]
    evidence_conflicts: list[str]
    coaching_points: list[str]
    recommended_next_action: str
    evidence_used: list[str]
    mock: bool
    # Additive, optional debug field: the actual sequence of LangGraph node
    # names executed for this request (e.g. ["Planner", "Evidence
    # Reconciliation", "Synthesizer"]). Proves a real StateGraph ran; not
    # part of the documented contract's required fields, so existing
    # consumers built against the pre-StateGraph contract are unaffected.
    graph_trace: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
