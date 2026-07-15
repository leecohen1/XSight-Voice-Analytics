"""Pydantic request/response models for the RAG service.

These preserve the production API contract documented in CLAUDE.md and
docs/api_contracts.md. Phase 6 implements validation and shape only —
POST /query returns a deterministic mock, not a real ChromaDB retrieval.
"""
from typing import Optional

from pydantic import BaseModel, Field


class CallMetadata(BaseModel):
    agent_name: Optional[str] = None
    call_duration_seconds: Optional[int] = Field(default=None, ge=0)
    sale_result: Optional[str] = None


class QueryRequest(BaseModel):
    transcript: str = Field(..., min_length=20, description="Full call transcript, speaker-tagged.")
    metadata: CallMetadata = Field(default_factory=CallMetadata)
    top_k: int = Field(default=3, ge=1, le=10)


class SimilarCall(BaseModel):
    call_id: str
    agent_name: str
    sale_result: str
    main_objection: str
    similarity_score: float
    reason: str


class QueryResponse(BaseModel):
    similar_calls: list[SimilarCall]
    insight: str
    citations: list[str]
    grounded: bool
    mock: bool


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
