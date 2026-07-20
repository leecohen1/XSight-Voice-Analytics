"""Deterministic pre-transcription input guardrail checks.

No NeMo Guardrails, no LLM — every check here is a fixed rule evaluated
directly against the request payload. This is the real (non-mock)
implementation of the pre-transcription stage of POST /check/input.
"""
from app.models import CheckInputRequest, CheckInputResponse, Checks

EXPECTED_STAGE = "pre_transcription"

ALLOWED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/ogg",
    "audio/webm",
}

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

# Case-insensitive substring matches against submission_metadata.notes only.
PROMPT_INJECTION_PHRASES = [
    "ignore previous instructions",
    "ignore all instructions",
    "system prompt",
    "developer message",
    "reveal your instructions",
    "jailbreak",
]


def _contains_prompt_injection(notes: str | None) -> bool:
    if not notes:
        return False
    lower = notes.lower()
    return any(phrase in lower for phrase in PROMPT_INJECTION_PHRASES)


def check_pre_transcription_input(payload: CheckInputRequest) -> CheckInputResponse:
    reasons: list[str] = []

    stage_valid = payload.stage == EXPECTED_STAGE
    if not stage_valid:
        reasons.append(f"stage must equal '{EXPECTED_STAGE}'.")

    filename = payload.file_metadata.filename
    file_present = bool(filename and filename.strip())
    if not file_present:
        reasons.append("file_metadata.filename is required and must not be empty.")

    mime_type = payload.file_metadata.mime_type
    mime_type_allowed = mime_type in ALLOWED_MIME_TYPES
    if not mime_type_allowed:
        reasons.append(f"mime_type '{mime_type}' is not an accepted audio type.")

    file_size = payload.file_metadata.file_size
    if file_size is None or file_size <= 0:
        file_size_allowed = False
        reasons.append("file_metadata.file_size must be greater than 0.")
    elif file_size > MAX_FILE_SIZE_BYTES:
        file_size_allowed = False
        reasons.append(f"file_metadata.file_size exceeds the {MAX_FILE_SIZE_BYTES} byte (100 MB) limit.")
    else:
        file_size_allowed = True

    agent_name = payload.submission_metadata.agent_name
    metadata_valid = bool(agent_name and agent_name.strip())
    if not metadata_valid:
        reasons.append("submission_metadata.agent_name is required and must not be empty.")

    prompt_injection_detected = _contains_prompt_injection(payload.submission_metadata.notes)
    if prompt_injection_detected:
        reasons.append("submission_metadata.notes contains a potential prompt-injection indicator.")

    checks = Checks(
        stage_valid=stage_valid,
        file_present=file_present,
        mime_type_allowed=mime_type_allowed,
        file_size_allowed=file_size_allowed,
        metadata_valid=metadata_valid,
        prompt_injection_detected=prompt_injection_detected,
    )

    passed = (
        stage_valid
        and file_present
        and mime_type_allowed
        and file_size_allowed
        and metadata_valid
        and not prompt_injection_detected
    )

    return CheckInputResponse(
        passed=passed,
        stage=EXPECTED_STAGE,
        checks=checks,
        reasons=reasons,
    )
