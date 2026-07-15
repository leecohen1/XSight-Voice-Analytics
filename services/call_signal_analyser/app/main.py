"""XSight Voice / Call Signal Analyser — FastAPI mock skeleton (Phase 6).

Real behavior (Phase 13): PyTorch feature-based classifier over transcript-
derived, structured-extraction, and lightweight audio-derived features. This
phase implements the API contract, validation, and error handling only —
POST /analyse-call returns a deterministic, documented mock (see
app/mock_rules.py), clearly labeled `"mock": true`. JSON input only in this
phase; multipart audio upload is not implemented yet.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.mock_rules import analyse
from app.models import AnalyseCallRequest, AnalyseCallResponse, HealthResponse

SERVICE_NAME = "call_signal_analyser"
SERVICE_VERSION = "0.1.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI(title="XSight Call Signal Analyser", version=SERVICE_VERSION)


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


@app.post("/analyse-call", response_model=AnalyseCallResponse)
async def analyse_call(payload: AnalyseCallRequest) -> AnalyseCallResponse:
    logger.info(
        "Mock /analyse-call received: intent=%s objection=%s closing=%s",
        payload.structured_fields.customer_intent,
        payload.structured_fields.main_objection,
        payload.structured_fields.closing_attempt,
    )
    return analyse(payload)
