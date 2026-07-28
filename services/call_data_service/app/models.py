"""Pydantic models for the Call Data Service.

Two distinct families live here, deliberately not merged:

1. The **stored record** (`AnalyzedCallRecord` and friends) -- the exact
   shape of one JSON object in S3 under the application prefix. Its
   `analysis` block keeps CLAUDE.md's documented final-output field names
   (snake_case) verbatim, so a record stays readable against the spec, and
   adds exactly two derived blocks (`attention`, `recovery_opportunity`).

2. The **Overview DTOs** -- the aggregated read contract the frontend
   consumes. These never appear in storage; they are computed per request
   by app/aggregation.py.

Ground Truth Rule (CLAUDE.md): a value that is genuinely unknown for a
record is `None`/`[]`, never a fabricated default. `confidence` on a seeded
historical call is `None` -- not `0.0` -- because the historical corpus
never measured one.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "1.0"

# ---- Enumerations (allowed values are fixed by the approved contract) ------

CallSource = Literal["historical_seed", "live_analysis"]
CallStatus = Literal["completed", "flagged", "human_review_required"]
CustomerSentiment = Literal["positive", "neutral", "negative"]
CallOutcome = Literal["Sale", "No Sale", "Follow-up Needed", "Uncertain"]
RiskLevel = Literal["Low", "Medium", "High"]
GuardrailStatus = Literal["pass", "flagged", "human_review_required"]
AttentionPriority = Literal["low", "medium", "high", "critical"]
AttentionCategory = Literal[
    "recoverable_opportunity",
    "human_review",
    "customer_dissatisfaction",
    "critical_coaching",
    "evidence_conflict",
    "low_priority",
]
Period = Literal["7d", "30d"]
TrendDirection = Literal["up", "down", "flat", "unknown"]

# Two ID shapes, one namespace. Historical seed rows keep the corpus's own
# CALL_001..CALL_024 identity so a citation in `similar_calls` and a stored
# record can refer to the same call; live calls are CALL_<uuid4>.
HISTORICAL_CALL_ID_RE = re.compile(r"^CALL_\d{3}$")
LIVE_CALL_ID_RE = re.compile(
    r"^CALL_[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def is_valid_call_id(call_id: str) -> bool:
    return bool(HISTORICAL_CALL_ID_RE.match(call_id) or LIVE_CALL_ID_RE.match(call_id))


def normalize_agent_name(raw: str) -> str:
    """Trim, collapse internal whitespace, lowercase.

    This is the grouping key for every per-agent aggregate. The display name
    is kept separately (`agent_name`) so 'sarah levi' and 'Sarah  Levi'
    aggregate together without the UI ever showing a mangled name.
    """
    return re.sub(r"\s+", " ", (raw or "").strip()).lower()


def _utc(value: datetime) -> datetime:
    """Coerce to timezone-aware UTC. A naive datetime is read as UTC rather
    than as the server's local time -- every window boundary in this service
    is UTC, and silently inheriting a machine's timezone would make the same
    record fall in different periods on different hosts."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


# ---- Stored record ---------------------------------------------------------


class SimilarCall(BaseModel):
    """One RAG citation. Field names match CLAUDE.md Component 3 exactly."""

    model_config = ConfigDict(extra="ignore")

    call_id: str
    agent_name: str = ""
    sale_result: str = ""
    main_objection: str = ""
    similarity_score: Optional[float] = None
    reason: str = ""


class Attention(BaseModel):
    """Deterministically derived -- never model-generated.

    See app/attention.py for the precedence order and the priority-score
    formula. Stored on the record (rather than recomputed at read time) so
    the Overview's ordering is stable and auditable per call.
    """

    model_config = ConfigDict(extra="ignore")

    required: bool = False
    priority: AttentionPriority = "low"
    priority_score: int = Field(default=0, ge=0, le=100)
    category: AttentionCategory = "low_priority"
    reason: Optional[str] = None


class RecoveryOpportunity(BaseModel):
    """Deterministically derived from outcome + lead quality + objection."""

    model_config = ConfigDict(extra="ignore")

    detected: bool = False
    confidence: Optional[float] = None
    reason: Optional[str] = None
    recommended_offer: Optional[str] = None
    recommended_follow_up_window: Optional[str] = None


class CallAnalysis(BaseModel):
    """CLAUDE.md's final output schema, plus the two derived blocks.

    `extra="ignore"` so a future additive field from the pipeline never
    makes an already-stored object unreadable.
    """

    model_config = ConfigDict(extra="ignore")

    transcript: str = ""
    call_summary: str = ""
    customer_intent: Optional[str] = None
    main_objection: Optional[str] = None
    customer_sentiment: Optional[CustomerSentiment] = None
    call_outcome: Optional[CallOutcome] = None
    agent_performance_score: Optional[int] = Field(default=None, ge=1, le=5)
    lead_quality_score: Optional[int] = Field(default=None, ge=1, le=5)
    similar_calls: list[SimilarCall] = Field(default_factory=list)
    coaching_feedback: list[str] = Field(default_factory=list)
    recommended_next_action: Optional[str] = None
    suggested_follow_up_email: str = ""
    routing_category: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    risk_level: Optional[RiskLevel] = None
    detected_signals: list[str] = Field(default_factory=list)
    limitations: str = ""
    guardrail_status: GuardrailStatus = "pass"
    attention: Attention = Field(default_factory=Attention)
    recovery_opportunity: RecoveryOpportunity = Field(default_factory=RecoveryOpportunity)


class AnalyzedCallRecord(BaseModel):
    """One stored S3 object under the application prefix."""

    model_config = ConfigDict(extra="ignore")

    schema_version: str = SCHEMA_VERSION
    call_id: str
    source: CallSource
    created_at: datetime
    call_date: Optional[date] = None
    agent_name: str
    agent_name_normalized: str = ""
    customer_name: Optional[str] = None
    status: CallStatus
    router_reasons: list[str] = Field(default_factory=list)
    analysis: CallAnalysis

    @field_validator("call_id")
    @classmethod
    def _check_call_id(cls, v: str) -> str:
        if not is_valid_call_id(v):
            raise ValueError(
                "call_id must be CALL_NNN (historical seed) or CALL_<uuid4> (live analysis)"
            )
        return v

    @field_validator("created_at")
    @classmethod
    def _check_created_at(cls, v: datetime) -> datetime:
        return _utc(v)

    @field_validator("agent_name")
    @classmethod
    def _check_agent_name(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", " ", (v or "").strip())
        if not cleaned:
            raise ValueError("agent_name must not be empty")
        return cleaned

    def model_post_init(self, __context: Any) -> None:
        # Always derive the grouping key from the display name rather than
        # trusting a caller-supplied value -- otherwise two records for the
        # same agent could disagree and silently split every aggregate.
        object.__setattr__(self, "agent_name_normalized", normalize_agent_name(self.agent_name))


# ---- Write API -------------------------------------------------------------


class CreateCallRequest(BaseModel):
    """POST /calls body. `call_id` is required and owned by the caller
    (n8n mints it before the pipeline runs) so the write is idempotent by
    call_id across retries."""

    model_config = ConfigDict(extra="ignore")

    schema_version: str = SCHEMA_VERSION
    call_id: str
    source: CallSource = "live_analysis"
    created_at: Optional[datetime] = None
    call_date: Optional[date] = None
    agent_name: str
    customer_name: Optional[str] = None
    status: Optional[CallStatus] = None
    router_reasons: list[str] = Field(default_factory=list)
    analysis: CallAnalysis

    @field_validator("call_id")
    @classmethod
    def _check_call_id(cls, v: str) -> str:
        if not is_valid_call_id(v):
            raise ValueError(
                "call_id must be CALL_NNN (historical seed) or CALL_<uuid4> (live analysis)"
            )
        return v


class CreateCallResponse(BaseModel):
    call_id: str
    key: str
    created: bool
    overwritten: bool


# ---- Read API --------------------------------------------------------------


class CallSummary(BaseModel):
    """A list row. Deliberately excludes `transcript` -- a list of 24+ full
    transcripts is megabytes the Calls screen never renders."""

    call_id: str
    source: CallSource
    created_at: datetime
    call_date: Optional[date] = None
    agent_name: str
    customer_name: Optional[str] = None
    status: CallStatus
    call_outcome: Optional[CallOutcome] = None
    agent_performance_score: Optional[int] = None
    lead_quality_score: Optional[int] = None
    confidence: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    guardrail_status: GuardrailStatus
    attention_required: bool = False
    attention_priority: AttentionPriority = "low"
    attention_priority_score: int = 0
    attention_category: AttentionCategory = "low_priority"


class CallListResponse(BaseModel):
    calls: list[CallSummary]
    count: int
    total_scanned: int
    skipped_malformed_records: int
    next_cursor: Optional[str] = None


# ---- Overview DTOs ---------------------------------------------------------


class KpiMetric(BaseModel):
    """One KPI with its previous-period comparison.

    `percentage_change` is None (never 0, never infinity) when the previous
    value is zero or unknown -- an undefined ratio is reported as undefined.
    """

    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    trend_direction: TrendDirection = "unknown"


class OverviewKpis(BaseModel):
    calls_analyzed: KpiMetric
    close_rate: KpiMetric
    average_agent_performance: KpiMetric
    average_lead_quality: KpiMetric
    calls_requiring_attention: KpiMetric
    improved_agents_count: KpiMetric


class TrendBucket(BaseModel):
    label: str
    start_date: date
    end_date: date
    calls_analyzed: int
    known_outcomes: int
    sales: int
    close_rate: Optional[float] = None


class ImprovedAgent(BaseModel):
    agent_name: str
    current_average_score: float
    previous_average_score: float
    improvement: float
    current_call_count: int
    previous_call_count: int


class AttentionCall(BaseModel):
    call_id: str
    created_at: datetime
    call_date: Optional[date] = None
    agent_name: str
    customer_name: Optional[str] = None
    call_outcome: Optional[CallOutcome] = None
    lead_quality_score: Optional[int] = None
    agent_performance_score: Optional[int] = None
    priority: AttentionPriority
    priority_score: int
    category: AttentionCategory
    reason: Optional[str] = None
    guardrail_status: GuardrailStatus


class RecentCall(BaseModel):
    call_id: str
    created_at: datetime
    call_date: Optional[date] = None
    agent_name: str
    customer_name: Optional[str] = None
    call_outcome: Optional[CallOutcome] = None
    agent_performance_score: Optional[int] = None
    lead_quality_score: Optional[int] = None
    guardrail_status: GuardrailStatus
    source: CallSource


class PeriodWindow(BaseModel):
    period: Period
    current_start: datetime
    current_end: datetime
    previous_start: datetime
    previous_end: datetime
    # Documented explicitly rather than left to the reader: the current
    # window is inclusive of "now" (and therefore of the current day);
    # the previous window is half-open and ends exactly where the current
    # window starts, so the two never overlap and never leave a gap.
    current_window_inclusive_of_now: bool = True


class DataQuality(BaseModel):
    loaded_records: int
    skipped_malformed_records: int
    current_period_records: int
    previous_period_records: int


class OverviewResponse(BaseModel):
    period: PeriodWindow
    generated_at: datetime
    executive_summary: str
    kpis: OverviewKpis
    close_rate_trend: list[TrendBucket]
    improved_agents: list[ImprovedAgent]
    attention_calls: list[AttentionCall]
    recent_calls: list[RecentCall]
    data_quality: DataQuality


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
