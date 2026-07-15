"""XSight Guardrails Service — FastAPI mock skeleton (Phase 6).

Real behavior (Phase 11): NeMo Guardrails (topic restrictions, unsafe
content, prompt-injection/jailbreak rails) + deterministic custom validation
rules. This phase implements the deterministic rules, the two-stage
POST /check/input contract, POST /check/output, validation, and error
handling — all responses are clearly labeled `"mock": true`. NeMo is not
integrated yet.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.mock_rules import check_output, check_post_transcription, check_pre_transcription
from app.models import CheckInputRequest, CheckResponse, HealthResponse, OutputCheckRequest

SERVICE_NAME = "guardrails_service"
SERVICE_VERSION = "0.1.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI(title="XSight Guardrails Service", version=SERVICE_VERSION)


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


@app.post("/check/input", response_model=CheckResponse, response_model_by_alias=True)
async def check_input(payload: CheckInputRequest) -> CheckResponse:
    if payload.stage == "pre_transcription":
        logger.info("Mock /check/input (pre_transcription) for filename=%s", payload.file_metadata.filename)
        return check_pre_transcription(payload)
    logger.info("Mock /check/input (post_transcription), transcript_len=%s", len(payload.transcript))
    return check_post_transcription(payload)


@app.post("/check/output", response_model=CheckResponse, response_model_by_alias=True)
async def check_output_endpoint(payload: OutputCheckRequest) -> CheckResponse:
    logger.info(
        "Mock /check/output: citations=%s historical_claims_present=%s confidence=%s",
        payload.citations, payload.historical_claims_present, payload.confidence,
    )
    return check_output(payload)
