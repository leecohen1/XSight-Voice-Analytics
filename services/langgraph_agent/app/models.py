"""Pydantic request/response models for the LangGraph Agent service.

Real behavior (Phase 14): a LangGraph graph — Planner Node -> Evidence
Reconciliation Node -> Synthesizer Node — reasoning over evidence n8n has
already fetched (this service never calls the RAG Service or Call Signal
Analyser itself). This phase implements the API contract and a deterministic
mock; see app/graph.py for the documented (not-yet-installed) graph plan.
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


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
