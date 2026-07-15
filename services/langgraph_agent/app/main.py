"""XSight LangGraph Agent Service — FastAPI mock skeleton (Phase 6).

Real behavior (Phase 14): a LangGraph graph (Planner -> Evidence
Reconciliation -> Synthesizer, LLM backend TBD) reasoning over evidence n8n
has already fetched from the RAG Service and Call Signal Analyser — this
service never calls those services itself. This phase implements the API
contract, validation, and error handling only — POST /agent/run returns a
deterministic mock (see app/graph.py), clearly labeled `"mock": true`. No
LangGraph graph is installed or executed in this phase.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.graph import run_mock_graph
from app.models import AgentRunRequest, AgentRunResponse, HealthResponse

SERVICE_NAME = "langgraph_agent"
SERVICE_VERSION = "0.1.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI(title="XSight LangGraph Agent Service", version=SERVICE_VERSION)


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


@app.post("/agent/run", response_model=AgentRunResponse)
async def agent_run(payload: AgentRunRequest) -> AgentRunResponse:
    logger.info("Mock /agent/run received: question=%r", payload.question)
    result = run_mock_graph(payload)
    return AgentRunResponse(**result)
