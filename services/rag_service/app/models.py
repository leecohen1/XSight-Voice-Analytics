"""Pydantic request/response models for the RAG service.

Preserves the production API contract documented in CLAUDE.md Component 3
(similar_calls / insight / citations) and docs/api_contracts.md, and adds
the two extensions this phase's real Amazon Bedrock Knowledge Base
implementation requires: an optional, allowlist-validated `filters` field on
the request, and a `retrieval_metadata` diagnostic block on the response.
Neither changes the shape of the three original fields — existing consumers
(n8n, LangGraph) are unaffected.
"""
from typing import Optional, Union

from pydantic import BaseModel, Field


class CallMetadata(BaseModel):
    """Informational context about the *current* call being analyzed — not
    a filter mechanism. See `filters` below for that."""
    agent_name: Optional[str] = None
    call_duration_seconds: Optional[int] = Field(default=None, ge=0)
    sale_result: Optional[str] = None


class QueryRequest(BaseModel):
    transcript: str = Field(..., min_length=20, description="Full call transcript, speaker-tagged.")
    metadata: CallMetadata = Field(default_factory=CallMetadata)
    top_k: int = Field(default=3, ge=1, le=10)
    filters: Optional[dict[str, Union[str, bool, int, float]]] = Field(
        default=None,
        description=(
            "Optional metadata filter criteria. Only field names marked "
            "allowed_for_filtering: true in "
            "services/rag_service/ingestion/metadata_schema.json are honored; "
            "unrecognized or invalid keys are dropped (reported in "
            "retrieval_metadata.dropped_filter_keys), not rejected. At most "
            "one filter is ever applied, per the Small-Corpus Filter Policy."
        ),
    )


class SimilarCall(BaseModel):
    call_id: str
    agent_name: str
    sale_result: str
    main_objection: str
    similarity_score: float
    reason: str


class RetrievalMetadata(BaseModel):
    knowledge_base_id: str
    search_type: str
    filter_requested: Optional[str] = None
    filter_applied: bool
    dropped_filter_keys: list[str] = Field(default_factory=list)
    results_returned: int
    results_above_threshold: int


class QueryResponse(BaseModel):
    similar_calls: list[SimilarCall]
    insight: str
    citations: list[str]
    grounded: bool
    retrieval_metadata: RetrievalMetadata


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
