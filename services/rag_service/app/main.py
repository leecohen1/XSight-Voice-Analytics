"""XSight RAG Service (Phase 12) — Amazon Bedrock Knowledge Base integration.

POST /query retrieves grounded historical-call evidence via
boto3 bedrock-agent-runtime Retrieve only (never RetrieveAndGenerate), from
the Knowledge Base provisioned over per-call documents in Amazon S3 (see
services/rag_service/ingestion/ for the pipeline that produced them from
data/historical_sales_calls.csv). This service performs retrieval and
deterministic response shaping only — it never calls Gemini or LangGraph.
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from botocore.exceptions import BotoCoreError
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.bedrock_client import (
    BedrockAccessDeniedError,
    BedrockThrottlingError,
    BedrockUnavailableError,
    BedrockValidationError,
    retrieve,
)
from app.config import ConfigurationError, load_settings
from app.filters import FilterBuildError, build_filter, load_filter_allowlist
from app.models import HealthResponse, QueryRequest, QueryResponse
from app.response_builder import build_response

SERVICE_NAME = "rag_service"
SERVICE_VERSION = "0.2.0"

# Local dev default: services/rag_service/app/main.py -> repo root is 3
# parents up, so data/ resolves naturally without any extra setup. In
# Docker, only ./app is copied into the image (see Dockerfile), so main.py
# sits just 2 levels below /, and parents[3] doesn't exist — guard against
# that instead of crashing at import time. docker-compose.yml mounts the
# repo's data/ directory at /data and sets
# HISTORICAL_CALLS_CSV_PATH=/data/historical_sales_calls.csv to match.
_file_parents = Path(__file__).resolve().parents
_DEFAULT_CSV_PATH = (
    _file_parents[3] / "data" / "historical_sales_calls.csv"
    if len(_file_parents) > 3
    else Path("/data/historical_sales_calls.csv")
)
HISTORICAL_CSV_PATH = Path(os.environ.get("HISTORICAL_CALLS_CSV_PATH", str(_DEFAULT_CSV_PATH)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(SERVICE_NAME)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # historical_sales_calls.csv itself is never read by this service — the
    # ingestion pipeline (services/rag_service/ingestion/) already converted
    # it into the documents this service retrieves from Bedrock. This check
    # is a startup sanity log only.
    if HISTORICAL_CSV_PATH.exists():
        logger.info("Historical dataset found at %s (reference only — retrieval goes through Bedrock).", HISTORICAL_CSV_PATH)
    else:
        logger.warning("Historical dataset not found at %s. Not required at runtime.", HISTORICAL_CSV_PATH)
    yield


app = FastAPI(title="XSight RAG Service", version=SERVICE_VERSION, lifespan=lifespan)


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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content=_error_body("INTERNAL_ERROR", "An unexpected error occurred.", []))


# Bedrock/configuration errors are raised as plain exceptions from the
# /query handler (not FastAPI HTTPExceptions) so app/bedrock_client.py and
# app/config.py stay framework-agnostic — these handlers are what translate
# them into stable HTTP responses. Every one of them logs the real
# exception server-side and returns only a generic, safe message to the
# client — no AWS stack trace, request ID, or internal detail ever crosses
# that boundary.
@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    logger.error("Configuration error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content=_error_body(
        "SERVICE_MISCONFIGURED", "The service is missing required configuration.", []))


@app.exception_handler(FilterBuildError)
async def filter_build_error_handler(request: Request, exc: FilterBuildError):
    logger.error("Filter builder error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content=_error_body(
        "SERVICE_MISCONFIGURED", "The service could not load its metadata filter policy.", []))


@app.exception_handler(BedrockAccessDeniedError)
async def bedrock_access_denied_handler(request: Request, exc: BedrockAccessDeniedError):
    logger.error("Bedrock access denied on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=502, content=_error_body(
        "UPSTREAM_ACCESS_DENIED", "The service could not authenticate to Amazon Bedrock.", []))


@app.exception_handler(BedrockValidationError)
async def bedrock_validation_error_handler(request: Request, exc: BedrockValidationError):
    logger.warning("Bedrock rejected the request on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=400, content=_error_body(
        "UPSTREAM_VALIDATION_ERROR", "Amazon Bedrock rejected the retrieval request.", []))


@app.exception_handler(BedrockThrottlingError)
async def bedrock_throttling_handler(request: Request, exc: BedrockThrottlingError):
    logger.warning("Bedrock throttled the request on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=429, content=_error_body(
        "UPSTREAM_THROTTLED", "Amazon Bedrock is throttling requests. Retry shortly.", []))


@app.exception_handler(BedrockUnavailableError)
async def bedrock_unavailable_handler(request: Request, exc: BedrockUnavailableError):
    logger.error("Bedrock unavailable on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content=_error_body(
        "UPSTREAM_UNAVAILABLE", "Amazon Bedrock did not respond successfully.", []))


@app.exception_handler(BotoCoreError)
async def botocore_error_handler(request: Request, exc: BotoCoreError):
    # Catch-all for botocore errors not already mapped by bedrock_client.py
    # (e.g. credential resolution failures) — still never a raw traceback.
    logger.exception("Unhandled botocore error on %s", request.url.path)
    return JSONResponse(status_code=503, content=_error_body(
        "UPSTREAM_UNAVAILABLE", "Amazon Bedrock did not respond successfully.", []))


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    logger.info("/query received: top_k=%s, transcript_len=%s, filters=%s",
                payload.top_k, len(payload.transcript), list((payload.filters or {}).keys()))

    settings = load_settings()  # raises ConfigurationError -> handled above
    allowlist = load_filter_allowlist()  # raises FilterBuildError -> handled above

    bedrock_filter, filter_requested, dropped_keys = build_filter(payload.filters, allowlist)
    if dropped_keys:
        logger.info("Dropped unsupported/invalid filter key(s): %s", dropped_keys)

    outcome = retrieve(
        settings=settings,
        query_text=payload.transcript,
        number_of_results=payload.top_k,
        bedrock_filter=bedrock_filter,
    )

    return build_response(
        outcome=outcome,
        knowledge_base_id=settings.knowledge_base_id,
        filter_requested=filter_requested,
        dropped_filter_keys=dropped_keys,
    )
