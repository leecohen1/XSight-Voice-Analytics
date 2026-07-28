"""XSight Call Data Service.

Owns business persistence and reads for analyzed sales calls, backed by
Amazon S3 under the application prefix (never the Bedrock Knowledge Base
prefix -- see app/repository.py's key guard).

Write path : n8n's post-Router persistence branch POSTs a completed analysis.
Read path  : the React Overview / Calls / Call Details screens.

This service never calls Gemini, AssemblyAI, Bedrock, or any other XSight
service. It stores what the pipeline already produced and aggregates it.
Error handling follows the same structured shape as the other four services:
{"error": {"code", "message", "details"}}, with no AWS internals in any body.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.aggregation import build_overview, is_analyzed, to_summary
from app.attention import derive_attention, derive_recovery_opportunity
from app.config import load_settings
from app.dependencies import get_repository
from app.errors import (
    ConfigurationError,
    MalformedRecordError,
    PrefixSafetyError,
    RecordNotFoundError,
    StorageUnavailableError,
)
from app.models import (
    AnalyzedCallRecord,
    CallListResponse,
    CreateCallRequest,
    CreateCallResponse,
    HealthResponse,
    OverviewResponse,
)
from app.repository import CallRepository, utc_now, window_bounds

SERVICE_NAME = "call_data_service"
SERVICE_VERSION = "1.0.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI(title="XSight Call Data Service", version=SERVICE_VERSION)

# The React dev server and the built frontend call this service directly.
# Permissive origins are consistent with the rest of this project's current
# no-authentication demo posture (documented in docs/FULL_PROJECT_AUDIT.md);
# adding auth is explicitly out of scope for this phase.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _error_body(code: str, message: str, details: list) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    logger.warning("Validation error on %s: %s", request.url.path, details)
    return JSONResponse(status_code=422, content=_error_body("VALIDATION_ERROR", "Request validation failed.", details))


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP error on %s: %s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content=_error_body("HTTP_ERROR", str(exc.detail), []))


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    logger.error("Configuration error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content=_error_body("SERVICE_MISCONFIGURED", "The service is missing required configuration.", []),
    )


@app.exception_handler(RecordNotFoundError)
async def not_found_handler(request: Request, exc: RecordNotFoundError):
    return JSONResponse(status_code=404, content=_error_body("CALL_NOT_FOUND", "No stored call matches that id.", []))


@app.exception_handler(PrefixSafetyError)
async def prefix_safety_handler(request: Request, exc: PrefixSafetyError):
    # Logged loudly: this can only fire on a real bug or a bad deployment
    # configuration, and it is the guard protecting the Bedrock corpus.
    logger.error("Prefix safety violation on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content=_error_body("STORAGE_KEY_REJECTED", "The requested storage location is not permitted.", []),
    )


@app.exception_handler(MalformedRecordError)
async def malformed_record_handler(request: Request, exc: MalformedRecordError):
    logger.warning("Malformed stored record on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=422,
        content=_error_body("MALFORMED_RECORD", "The stored record could not be read as a valid call.", []),
    )


@app.exception_handler(StorageUnavailableError)
async def storage_unavailable_handler(request: Request, exc: StorageUnavailableError):
    logger.error("Storage unavailable on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content=_error_body("STORAGE_UNAVAILABLE", "Object storage did not respond successfully.", []),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content=_error_body("INTERNAL_ERROR", "An unexpected error occurred.", []))


# ---- routes ----------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)


def _derive_blocks(payload: CreateCallRequest) -> AnalyzedCallRecord:
    """Build the stored record, deriving `attention` and
    `recovery_opportunity` here rather than trusting the caller.

    n8n may send them (its own deterministic Code node computes the same
    rules for the immediate response), but this service recomputes from the
    same inputs so the stored record can never drift from the documented
    formula -- and so an LLM can never influence routing severity.
    """
    analysis = payload.analysis
    status = payload.status
    if status is None:
        status = (
            "human_review_required"
            if analysis.guardrail_status == "human_review_required"
            else "flagged"
            if analysis.guardrail_status == "flagged"
            else "completed"
        )

    attention = derive_attention(
        call_outcome=analysis.call_outcome,
        customer_sentiment=analysis.customer_sentiment,
        agent_performance_score=analysis.agent_performance_score,
        lead_quality_score=analysis.lead_quality_score,
        risk_level=analysis.risk_level,
        confidence=analysis.confidence,
        guardrail_status=analysis.guardrail_status,
        router_reasons=payload.router_reasons,
    )
    recovery = derive_recovery_opportunity(
        call_outcome=analysis.call_outcome,
        lead_quality_score=analysis.lead_quality_score,
        main_objection=analysis.main_objection,
        confidence=analysis.confidence,
        attention=attention,
    )
    enriched = analysis.model_copy(update={"attention": attention, "recovery_opportunity": recovery})

    created_at = payload.created_at or utc_now()
    call_date = payload.call_date or created_at.astimezone(timezone.utc).date()

    return AnalyzedCallRecord(
        schema_version=payload.schema_version,
        call_id=payload.call_id,
        source=payload.source,
        created_at=created_at,
        call_date=call_date,
        agent_name=payload.agent_name,
        customer_name=payload.customer_name,
        status=status,
        router_reasons=payload.router_reasons,
        analysis=enriched,
    )


@app.post("/calls", response_model=CreateCallResponse, status_code=201)
async def create_call(
    payload: CreateCallRequest, repo: CallRepository = Depends(get_repository)
) -> CreateCallResponse:
    record = _derive_blocks(payload)
    key, overwritten = repo.put_record(record)
    logger.info(
        "Persisted call %s (source=%s, status=%s, overwritten=%s)",
        record.call_id,
        record.source,
        record.status,
        overwritten,
    )
    return CreateCallResponse(call_id=record.call_id, key=key, created=not overwritten, overwritten=overwritten)


@app.get("/calls", response_model=CallListResponse)
async def list_calls(
    repo: CallRepository = Depends(get_repository),
    limit: Optional[int] = Query(default=None, ge=1, le=1000),
    cursor: Optional[str] = Query(default=None, description="call_id to resume after, from a prior next_cursor"),
    agent_name: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
) -> CallListResponse:
    settings = load_settings()
    effective_limit = min(limit or settings.default_list_limit, settings.max_list_limit)

    result = repo.load_all()
    records = [r for r in result.records if is_analyzed(r)]

    if agent_name:
        from app.models import normalize_agent_name

        wanted = normalize_agent_name(agent_name)
        records = [r for r in records if r.agent_name_normalized == wanted]
    if status:
        records = [r for r in records if r.status == status]
    if source:
        records = [r for r in records if r.source == source]
    if from_date:
        records = [r for r in records if r.created_at.date() >= from_date]
    if to_date:
        records = [r for r in records if r.created_at.date() <= to_date]

    records.sort(key=lambda r: (r.created_at, r.call_id), reverse=True)
    total_scanned = len(records)

    if cursor:
        index = next((i for i, r in enumerate(records) if r.call_id == cursor), None)
        records = records[index + 1 :] if index is not None else []

    page = records[:effective_limit]
    next_cursor = page[-1].call_id if len(records) > effective_limit and page else None

    return CallListResponse(
        calls=[to_summary(r) for r in page],
        count=len(page),
        total_scanned=total_scanned,
        skipped_malformed_records=result.skipped_count,
        next_cursor=next_cursor,
    )


@app.get("/calls/{call_id}", response_model=AnalyzedCallRecord)
async def get_call(call_id: str, repo: CallRepository = Depends(get_repository)) -> AnalyzedCallRecord:
    return repo.get_by_call_id(call_id)


@app.get("/overview", response_model=OverviewResponse)
async def overview(
    repo: CallRepository = Depends(get_repository),
    period: str = Query(default="7d", pattern="^(7d|30d)$"),
) -> OverviewResponse:
    now = utc_now()
    current_start, current_end, previous_start, previous_end = window_bounds(period, now)

    # Fetch only the month partitions the two windows actually touch.
    result = repo.load_range(previous_start, current_end)

    return build_overview(
        all_records=result.records,
        skipped_count=result.skipped_count,
        period=period,
        current_start=current_start,
        current_end=current_end,
        previous_start=previous_start,
        previous_end=previous_end,
        generated_at=now,
    )
