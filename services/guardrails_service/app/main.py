"""XSight Guardrails Service — pre-transcription input validation.

First real (non-mock) implementation: deterministic checks only, no
NeMo Guardrails, no LLM. Covers POST /check/input (pre_transcription
stage) and GET /health.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.guardrails import check_pre_transcription_input
from app.models import CheckInputRequest, CheckInputResponse, HealthResponse

SERVICE_NAME = "guardrails_service"
SERVICE_VERSION = "0.2.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI(title="XSight Guardrails Service", version=SERVICE_VERSION)


def _error_body(code: str, message: str, details: list) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    logger.warning("Validation error on %s", request.url.path)
    return JSONResponse(status_code=422, content=_error_body("VALIDATION_ERROR", "Request validation failed.", details))


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP error on %s: %s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content=_error_body("HTTP_ERROR", str(exc.detail), []))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak internal exception details or stack traces to the caller.
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content=_error_body("INTERNAL_ERROR", "An unexpected error occurred.", []))


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post("/check/input", response_model=CheckInputResponse, response_model_by_alias=True)
async def check_input(payload: CheckInputRequest) -> CheckInputResponse:
    logger.info("check/input received (file_present=%s)", bool(payload.file_metadata.filename))
    return check_pre_transcription_input(payload)
