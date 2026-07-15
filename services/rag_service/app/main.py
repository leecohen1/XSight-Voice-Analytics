"""XSight RAG Service — FastAPI mock skeleton (Phase 6).

Real behavior (Phase 12): LangChain + ChromaDB + HuggingFace embeddings +
Llama.cpp, retrieving grounded historical-call evidence from
data/historical_sales_calls.csv via ChromaDB. This phase implements the API
contract, validation, and error handling only — POST /query returns a
deterministic mock response, clearly labeled `"mock": true`, and does not
read ChromaDB or ingest the CSV.
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import HealthResponse, QueryRequest, QueryResponse, SimilarCall

SERVICE_NAME = "rag_service"
SERVICE_VERSION = "0.1.0"

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
    # Optional confirmation only, per Phase 6 scope — never read/ingested here.
    if HISTORICAL_CSV_PATH.exists():
        logger.info("Historical dataset found at %s (not read — ingestion is Phase 12).", HISTORICAL_CSV_PATH)
    else:
        logger.warning("Historical dataset not found at %s. Not required for mock responses.", HISTORICAL_CSV_PATH)
    yield


app = FastAPI(title="XSight RAG Service", version=SERVICE_VERSION, lifespan=lifespan)

# Small, hardcoded mock corpus for deterministic responses only.
# NOT sourced from data/historical_sales_calls.csv — real ingestion is Phase 12.
_MOCK_POOL = [
    SimilarCall(
        call_id="CALL_007", agent_name="Daniel Cohen", sale_result="Sale",
        main_objection="price", similarity_score=0.89,
        reason="Mock similarity result based on a price objection resolved through a quantified reframe.",
    ),
    SimilarCall(
        call_id="CALL_002", agent_name="Sarah Levi", sale_result="Sale",
        main_objection="integration", similarity_score=0.81,
        reason="Mock similarity result based on a resolved integration concern.",
    ),
    SimilarCall(
        call_id="CALL_015", agent_name="Michael Ben-David", sale_result="No Sale",
        main_objection="price", similarity_score=0.75,
        reason="Mock similarity result based on a price objection tied to the customer's own ROI model.",
    ),
    SimilarCall(
        call_id="CALL_010", agent_name="Daniel Cohen", sale_result="No Sale",
        main_objection="authority", similarity_score=0.69,
        reason="Mock similarity result based on an authority/decision-maker gap.",
    ),
    SimilarCall(
        call_id="CALL_023", agent_name="Noa Friedman", sale_result="Follow-up Needed",
        main_objection="price", similarity_score=0.64,
        reason="Mock similarity result based on a high-intent call left open by weak follow-through.",
    ),
]


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


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    logger.info("Mock /query received: top_k=%s, transcript_len=%s", payload.top_k, len(payload.transcript))

    similar_calls = _MOCK_POOL[: payload.top_k]
    citations = [c.call_id for c in similar_calls]

    insight = (
        f"Mock grounded insight referencing {len(citations)} historical call(s) "
        f"({', '.join(citations)}). Real retrieval is not implemented yet."
    )

    return QueryResponse(
        similar_calls=similar_calls,
        insight=insight,
        citations=citations,
        grounded=True,
        mock=True,
    )
