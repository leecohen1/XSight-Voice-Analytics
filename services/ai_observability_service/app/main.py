"""XSight AI Observability Service.

Records one Langfuse trace (with nested span/generation observations) per
analyzed call, and serves frontend-safe, product-specific aggregation
endpoints that combine Langfuse-measured LLM usage/cost with locally
configured fixed infrastructure cost. See README.md for the full
accounting-terminology explanation and the architecture decision record
(why this service was refactored from a standalone SQLite usage-tracking
service into a Langfuse adapter + fixed-cost store).

Follows the same FastAPI conventions as the other four XSight services:
plain FastAPI + Pydantic, no ORM, the same structured error shape, the
same GET /health contract.

**Langfuse is disabled by default in this codebase.** No real Langfuse
account was created as part of this work — LANGFUSE_PUBLIC_KEY/SECRET_KEY
are unset placeholders in .env.example only. Every endpoint below is
written to behave correctly (never crash, never fabricate a number)
whether or not those credentials are ever configured.
"""
import logging
import sqlite3
from decimal import Decimal
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import repository
from app.config import load_settings
from app.db import get_connection
from app.langfuse_client import ObservabilityClient, build_observability_client
from app.langfuse_query_adapter import (
    LangfuseQueryClient,
    normalize_call_list,
    normalize_daily_buckets,
    normalize_grouped_breakdown,
    normalize_summary,
)
from app.models import (
    CallDetailResponse,
    CallListResponse,
    CostBreakdownResponse,
    DailyUsageResponse,
    HealthResponse,
    ProviderBreakdownResponse,
    RejectedEventResult,
    StageBreakdownResponse,
    TraceIngestRequest,
    TraceIngestResponse,
    UsageSummaryResponse,
)
from app.time_utils import days_in_month, resolve_period
from app.trace_recorder import record_call_trace
from app.validation import validate_event

SERVICE_NAME = "ai_observability_service"
SERVICE_VERSION = "0.2.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(SERVICE_NAME)

settings = load_settings()

app = FastAPI(title="XSight AI Observability Service", version=SERVICE_VERSION)


def _error_body(code: str, message: str, details: list) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


class BatchTooLargeError(RuntimeError):
    """A batch exceeded MAX_EVENTS_PER_BATCH — rejected before any event in
    it is processed."""


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    logger.warning("Validation error on %s", request.url.path)
    return JSONResponse(status_code=422, content=_error_body("VALIDATION_ERROR", "Request validation failed.", details))


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP error on %s: %s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content=_error_body("HTTP_ERROR", str(exc.detail), []))


@app.exception_handler(BatchTooLargeError)
async def batch_too_large_handler(request: Request, exc: BatchTooLargeError):
    logger.warning("Batch too large on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=413, content=_error_body("BATCH_TOO_LARGE", str(exc), []))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content=_error_body("INTERNAL_ERROR", "An unexpected error occurred.", []))


def get_db() -> sqlite3.Connection:
    """FastAPI dependency yielding a per-request SQLite connection (now
    holding only pricing_config + infrastructure_cost_config). Tests
    override this (see conftest.py) to point at an isolated temporary
    database file instead of the configured production path."""
    conn = get_connection(settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_observability_client() -> ObservabilityClient:
    """Built fresh per request from current settings — cheap (no network
    call happens at construction time; see app/langfuse_client.py) and
    keeps this dependency trivially overridable in tests."""
    return build_observability_client(settings)


def get_query_client(
    observability_client: ObservabilityClient = Depends(get_observability_client),
) -> LangfuseQueryClient:
    return LangfuseQueryClient(observability_client)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)


# --- Write path: record one call's trace ------------------------------------


@app.post("/observability/events", response_model=TraceIngestResponse)
async def post_observability_events(
    payload: TraceIngestRequest,
    conn: sqlite3.Connection = Depends(get_db),
    observability_client: ObservabilityClient = Depends(get_observability_client),
):
    if len(payload.events) > settings.max_events_per_batch:
        raise BatchTooLargeError(
            f"Batch contains {len(payload.events)} events, exceeding the configured "
            f"maximum of {settings.max_events_per_batch}."
        )

    validated_events = []
    rejected: list[RejectedEventResult] = []
    for raw_event in payload.events:
        validated, reasons = validate_event(raw_event)
        if validated is None:
            idem = raw_event.get("idempotency_key") if isinstance(raw_event, dict) else None
            rejected.append(RejectedEventResult(idempotency_key=idem, reasons=reasons))
        else:
            validated_events.append(validated)

    result = record_call_trace(
        client=observability_client,
        conn=conn,
        call_id=payload.call_id,
        workflow_execution_id=payload.workflow_execution_id,
        trace_metadata=payload.trace_metadata,
        events=validated_events,
    )

    return TraceIngestResponse(
        call_id=payload.call_id,
        workflow_execution_id=payload.workflow_execution_id,
        trace_id=result.trace_id,
        observability_enabled=result.observability_enabled,
        recorded_stage_names=result.recorded_stage_names,
        rejected=rejected,
        recorded_count=len(result.recorded_stage_names),
        rejected_count=len(rejected),
    )


# --- Read / aggregation path -------------------------------------------------


def _cost_str(value: Optional[Decimal]) -> Optional[str]:
    return str(value) if value is not None else None


def _allocated_fixed_cost(conn: sqlite3.Connection, period_start: str, period_end: str, range_: Optional[str]) -> Decimal:
    allocated = repository.get_flat_monthly_infrastructure_cost(conn, period_start, period_end)
    if range_ == "today":
        days = days_in_month(period_start)
        allocated = allocated / Decimal(days) if days else Decimal("0")
    return allocated


@app.get("/usage/summary", response_model=UsageSummaryResponse, deprecated=True, include_in_schema=False)
@app.get("/observability/summary", response_model=UsageSummaryResponse)
async def observability_summary(
    range: Optional[str] = None,
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
    provider: Optional[str] = None,
    pipeline_stage: Optional[str] = None,
    model: Optional[str] = None,
    use_case: Optional[str] = None,
    conn: sqlite3.Connection = Depends(get_db),
    query_client: LangfuseQueryClient = Depends(get_query_client),
):
    period_start, period_end = resolve_period(range, from_, to)
    metrics = query_client.fetch_metrics(period_start=period_start, period_end=period_end)
    summary = normalize_summary(metrics)

    allocated_fixed = _allocated_fixed_cost(conn, period_start, period_end, range)
    # Variable cost is not yet derivable from a mocked/disabled Langfuse
    # connection in this phase — see README "Known limitations". Never
    # fabricated as 0; kept explicitly None until real integration exists.
    variable_cost = None
    total_cost = (variable_cost or Decimal("0")) + allocated_fixed if allocated_fixed else variable_cost

    return UsageSummaryResponse(
        total_input_tokens=summary["total_input_tokens"],
        total_output_tokens=summary["total_output_tokens"],
        total_tokens=summary["total_tokens"],
        estimated_variable_cost_usd=_cost_str(variable_cost),
        allocated_fixed_cost_usd=_cost_str(allocated_fixed),
        estimated_total_cost_usd=_cost_str(total_cost),
        calls_analyzed=summary["calls_analyzed"],
        events_count=summary["events_count"],
        pricing_gap_count=0 if metrics else 1,
        period_start=period_start,
        period_end=period_end,
        observability_enabled=query_client._observability_client.enabled,
    )


@app.get("/observability/daily", response_model=DailyUsageResponse)
async def observability_daily(
    range: Optional[str] = None,
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
    query_client: LangfuseQueryClient = Depends(get_query_client),
):
    period_start, period_end = resolve_period(range, from_, to)
    metrics = query_client.fetch_metrics(period_start=period_start, period_end=period_end, dimensions=["date"])
    days = normalize_daily_buckets(metrics)
    return DailyUsageResponse(
        period_start=period_start,
        period_end=period_end,
        days=days,
        observability_enabled=query_client._observability_client.enabled,
    )


@app.get("/observability/by-stage", response_model=StageBreakdownResponse)
async def observability_by_stage(
    range: Optional[str] = None,
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
    query_client: LangfuseQueryClient = Depends(get_query_client),
):
    period_start, period_end = resolve_period(range, from_, to)
    metrics = query_client.fetch_metrics(period_start=period_start, period_end=period_end, dimensions=["pipeline_stage"])
    stages = normalize_grouped_breakdown(metrics, "pipeline_stage")
    return StageBreakdownResponse(
        period_start=period_start,
        period_end=period_end,
        stages=stages,
        observability_enabled=query_client._observability_client.enabled,
    )


@app.get("/observability/by-provider", response_model=ProviderBreakdownResponse)
async def observability_by_provider(
    range: Optional[str] = None,
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
    query_client: LangfuseQueryClient = Depends(get_query_client),
):
    period_start, period_end = resolve_period(range, from_, to)
    metrics = query_client.fetch_metrics(period_start=period_start, period_end=period_end, dimensions=["provider"])
    providers = normalize_grouped_breakdown(metrics, "provider")
    return ProviderBreakdownResponse(
        period_start=period_start,
        period_end=period_end,
        providers=providers,
        observability_enabled=query_client._observability_client.enabled,
    )


@app.get("/observability/calls", response_model=CallListResponse)
async def observability_calls(
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    query_client: LangfuseQueryClient = Depends(get_query_client),
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    observations = query_client.fetch_observations(
        period_start=from_ or "0001-01-01T00:00:00+00:00", period_end=to or "9999-01-01T00:00:00+00:00", limit=page_size
    )
    calls = normalize_call_list(observations)
    if status:
        calls = [c for c in calls if c["status"] == status]
    return CallListResponse(
        calls=calls,
        page=page,
        page_size=page_size,
        total_count=len(calls),
        observability_enabled=query_client._observability_client.enabled,
    )


@app.get("/observability/calls/{call_id}", response_model=CallDetailResponse)
async def observability_call_detail(call_id: str, query_client: LangfuseQueryClient = Depends(get_query_client)):
    observations = query_client.fetch_observations(
        period_start="0001-01-01T00:00:00+00:00", period_end="9999-01-01T00:00:00+00:00", trace_id=call_id
    )
    if not observations:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No Langfuse trace data found for call_id '{call_id}' "
                "(observability may be disabled, or no matching trace exists)."
            ),
        )

    events = [
        {
            "provider": obs.get("provider", "unknown"),
            "service": obs.get("service", "unknown"),
            "model": obs.get("model"),
            "pipeline_stage": obs.get("name", "unknown"),
            "input_tokens": (obs.get("usage_details") or {}).get("input"),
            "output_tokens": (obs.get("usage_details") or {}).get("output"),
            "total_tokens": None,
            "audio_duration_seconds": (obs.get("usage_details") or {}).get("duration_seconds"),
            "latency_ms": obs.get("latency_ms"),
            "estimated_variable_cost_usd": (obs.get("cost_details") or {}).get("total"),
            "status": "failed" if obs.get("level") == "ERROR" else "success",
            "occurred_at": obs.get("start_time"),
            "metadata": obs.get("metadata") or {},
        }
        for obs in observations
    ]
    total_input = sum(e["input_tokens"] or 0 for e in events) or None
    total_output = sum(e["output_tokens"] or 0 for e in events) or None

    return CallDetailResponse(
        call_id=call_id,
        trace_id=call_id,
        events=events,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=(total_input or 0) + (total_output or 0) or None,
        estimated_variable_cost_usd=None,
        pricing_gap_count=0,
        observability_enabled=query_client._observability_client.enabled,
    )


@app.get("/observability/cost-breakdown", response_model=CostBreakdownResponse)
async def observability_cost_breakdown(
    range: Optional[str] = None,
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
    allocation_method: str = "flat_monthly",
    conn: sqlite3.Connection = Depends(get_db),
    query_client: LangfuseQueryClient = Depends(get_query_client),
):
    period_start, period_end = resolve_period(range, from_, to)
    metrics = query_client.fetch_metrics(period_start=period_start, period_end=period_end)
    summary = normalize_summary(metrics)

    if allocation_method == "per_call_share":
        monthly_fixed = repository.get_per_call_share_infrastructure_cost(conn, period_start, period_end)
        calls_this_period = summary["calls_analyzed"]
        allocated_fixed = monthly_fixed if calls_this_period > 0 else Decimal("0")
        if range == "today":
            days = days_in_month(period_start)
            allocated_fixed = allocated_fixed / Decimal(days) if days else Decimal("0")
    else:
        allocated_fixed = _allocated_fixed_cost(conn, period_start, period_end, range)

    variable_cost = None  # not yet derivable -- see observability_summary's comment
    total_cost = (variable_cost or Decimal("0")) + allocated_fixed if allocated_fixed else variable_cost

    return CostBreakdownResponse(
        period_start=period_start,
        period_end=period_end,
        estimated_variable_cost_usd=_cost_str(variable_cost),
        allocated_fixed_cost_usd=_cost_str(allocated_fixed),
        estimated_total_cost_usd=_cost_str(total_cost),
        pricing_gap_count=0 if metrics else 1,
        fixed_cost_allocation_method=allocation_method,
        observability_enabled=query_client._observability_client.enabled,
    )
