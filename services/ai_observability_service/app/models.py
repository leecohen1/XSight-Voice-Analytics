"""Pydantic request/response models for the AI Observability Service.

Design note on `events`: individual batch items are accepted as loosely-typed
`dict`s (`List[Dict[str, Any]]`), not a strict per-item Pydantic model —
see app/validation.py's docstring for why (one malformed event must not
invalidate the whole batch).

Cost fields are returned as decimal *strings*, never floats — see
app/pricing.py.

**Architecture note (Langfuse adoption):** the write-path models below
(`TraceIngestRequest`/`TraceIngestResponse`) replace the old
`UsageEventBatchRequest`/`UsageEventBatchResponse`, which reported a
locally-assigned SQLite row `id` per event. There is no local row per
event anymore — each event becomes a Langfuse span/generation observation
nested under one trace per call, so the response instead reports the
`trace_id` and which stage names were recorded vs. rejected. The
read-path models (`UsageSummaryResponse` and friends) keep their EXACT
prior shape and field names deliberately — the frontend contract must not
change just because the data source moved from local SQLite to Langfuse;
only `app/main.py`'s implementation of how these get populated changed.
"""
from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


# --- Write path (trace/observation ingestion) ------------------------------


class TraceIngestRequest(BaseModel):
    call_id: str = Field(..., min_length=1, max_length=200)
    workflow_execution_id: Optional[str] = Field(default=None, max_length=200)
    # Trace-level context (see app/metadata_safety.py's TRACE_METADATA_ALLOWED_KEYS
    # and CLAUDE.md's "Approved Observability Data Model") -- e.g. environment,
    # workflow_version, final_status, human_review_required, use_case.
    trace_metadata: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(..., min_length=1)


class RejectedEventResult(BaseModel):
    idempotency_key: Optional[str] = None
    reasons: list[str]


class TraceIngestResponse(BaseModel):
    call_id: str
    workflow_execution_id: Optional[str] = None
    trace_id: str
    observability_enabled: bool
    recorded_stage_names: list[str]
    rejected: list[RejectedEventResult]
    recorded_count: int
    rejected_count: int


# --- Read / aggregation path (Langfuse-backed, combined with local fixed cost) --


class UsageSummaryResponse(BaseModel):
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_variable_cost_usd: Optional[str] = None
    allocated_fixed_cost_usd: Optional[str] = None
    estimated_total_cost_usd: Optional[str] = None
    calls_analyzed: int
    events_count: int
    pricing_gap_count: int
    period_start: str
    period_end: str
    currency: str = "USD"
    observability_enabled: bool = False


class DailyBucket(BaseModel):
    date: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_variable_cost_usd: Optional[str] = None
    calls_analyzed: int
    pricing_gap_count: int = 0


class DailyUsageResponse(BaseModel):
    period_start: str
    period_end: str
    days: list[DailyBucket]
    observability_enabled: bool = False


class StageBreakdownItem(BaseModel):
    pipeline_stage: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_variable_cost_usd: Optional[str] = None
    events_count: int
    pricing_gap_count: int = 0


class StageBreakdownResponse(BaseModel):
    period_start: str
    period_end: str
    stages: list[StageBreakdownItem]
    observability_enabled: bool = False


class ProviderBreakdownItem(BaseModel):
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_variable_cost_usd: Optional[str] = None
    events_count: int
    pricing_gap_count: int = 0


class ProviderBreakdownResponse(BaseModel):
    period_start: str
    period_end: str
    providers: list[ProviderBreakdownItem]
    observability_enabled: bool = False


class CallListItem(BaseModel):
    call_id: str
    analyzed_at: Optional[str] = None
    audio_duration_seconds: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_variable_cost_usd: Optional[str] = None
    status: str
    pricing_gap_count: int = 0


class CallListResponse(BaseModel):
    calls: list[CallListItem]
    page: int
    page_size: int
    total_count: int
    observability_enabled: bool = False


class CallEventDetail(BaseModel):
    provider: str
    service: str
    model: Optional[str] = None
    pipeline_stage: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    audio_duration_seconds: Optional[float] = None
    latency_ms: Optional[int] = None
    estimated_variable_cost_usd: Optional[str] = None
    status: str
    occurred_at: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CallDetailResponse(BaseModel):
    call_id: str
    trace_id: Optional[str] = None
    events: list[CallEventDetail]
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_variable_cost_usd: Optional[str] = None
    pricing_gap_count: int = 0
    observability_enabled: bool = False


class CostBreakdownResponse(BaseModel):
    period_start: str
    period_end: str
    estimated_variable_cost_usd: Optional[str] = None
    allocated_fixed_cost_usd: Optional[str] = None
    estimated_total_cost_usd: Optional[str] = None
    pricing_gap_count: int = 0
    fixed_cost_allocation_method: Optional[str] = None
    currency: str = "USD"
    observability_enabled: bool = False
    labels: list[str] = Field(
        default_factory=lambda: [
            "All cost figures are estimates derived from measured usage and configured "
            "provider pricing — not an actual provider invoice.",
            "estimated_variable_cost_usd reflects Langfuse-measured token/duration/request "
            "usage only.",
            "allocated_fixed_cost_usd is a share of fixed infrastructure cost, not a "
            "cost caused by any individual call.",
        ]
    )
