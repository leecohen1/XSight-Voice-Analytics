"""Deterministic mock guardrail rules (Phase 6).

Deterministic custom validation rules only — NeMo Guardrails (topic
restrictions, unsafe content, prompt-injection/jailbreak rails) is not
integrated in this phase (Phase 11). Every rule below is documented and
keyword-based, so results are fully repeatable.
"""
from pathlib import Path

from app.models import (
    CheckResponse,
    OutputCheckRequest,
    PostTranscriptionInput,
    PreTranscriptionInput,
)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}
ALLOWED_MIME_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/mp4", "audio/flac", "audio/ogg",
}
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_DURATION_SECONDS = 1800  # 30 minutes

MIN_TRANSCRIPT_LENGTH = 20  # characters

PROMPT_INJECTION_PHRASES = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard the above",
    "disregard previous instructions",
    "you are now",
    "system prompt",
    "act as",
    "jailbreak",
    "reveal your instructions",
]

SALES_RELEVANCE_KEYWORDS = [
    "price", "pricing", "product", "demo", "contract", "sign", "platform",
    "proposal", "subscription", "deal", "purchase", "sales", "pipeline",
    "crm", "quote", "budget", "onboarding", "vendor", "objection",
]
# Deliberately excludes "agent"/"customer" — those appear as speaker-tag
# prefixes in every transcript, so including them would make this check
# always pass regardless of actual topical content.

PLACEHOLDER_PATTERNS = [
    "lorem ipsum", "placeholder", "[insert", "todo:", "xxxxx",
    "tbd - not implemented", "n/a - not implemented", "fake data",
]


def _find_first(text: str, phrases: list[str]) -> str | None:
    lower = text.lower()
    for phrase in phrases:
        if phrase in lower:
            return phrase
    return None


def _collect_strings(value) -> list[str]:
    """Recursively collect every string value out of a (possibly nested) dict/list."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out = []
        for v in value.values():
            out.extend(_collect_strings(v))
        return out
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(_collect_strings(v))
        return out
    return []


def check_pre_transcription(payload: PreTranscriptionInput) -> CheckResponse:
    flags: list[str] = []
    reasons: list[str] = []
    fm = payload.file_metadata

    if not fm.filename.strip():
        flags.append("missing_filename")
        reasons.append("filename is required.")
    else:
        ext = Path(fm.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            flags.append("unsupported_extension")
            reasons.append(f"File extension '{ext or '(none)'}' is not in the allowed list {sorted(ALLOWED_EXTENSIONS)}.")

    if fm.mime_type not in ALLOWED_MIME_TYPES:
        flags.append("unsupported_mime_type")
        reasons.append(f"MIME type '{fm.mime_type}' is not in the allowed list {sorted(ALLOWED_MIME_TYPES)}.")

    if fm.size_bytes <= 0:
        flags.append("empty_file")
        reasons.append("File size must be greater than zero.")
    elif fm.size_bytes > MAX_FILE_SIZE_BYTES:
        flags.append("file_too_large")
        reasons.append(f"File size {fm.size_bytes} bytes exceeds the {MAX_FILE_SIZE_BYTES} byte limit.")

    if fm.duration_seconds is not None and fm.duration_seconds > MAX_DURATION_SECONDS:
        flags.append("duration_too_long")
        reasons.append(f"Duration {fm.duration_seconds}s exceeds the {MAX_DURATION_SECONDS}s limit.")

    sm = payload.submission_metadata
    if not sm.agent_name or not sm.agent_name.strip():
        flags.append("missing_agent_name")
        reasons.append("submission_metadata.agent_name is required.")
    if not sm.call_date or not sm.call_date.strip():
        flags.append("missing_call_date")
        reasons.append("submission_metadata.call_date is required.")

    passed = not flags
    return CheckResponse(
        passed=passed,
        reason="; ".join(reasons),
        flags=flags,
        safe_text=None,
        human_review_required=False,
        mock=True,
    )


def check_post_transcription(payload: PostTranscriptionInput) -> CheckResponse:
    flags: list[str] = []
    reasons: list[str] = []
    transcript = payload.transcript or ""
    stripped = transcript.strip()

    if not stripped:
        flags.append("empty_transcript")
        reasons.append("transcript must not be empty.")
    elif len(stripped) < MIN_TRANSCRIPT_LENGTH:
        flags.append("transcript_too_short")
        reasons.append(f"transcript is shorter than the {MIN_TRANSCRIPT_LENGTH}-character minimum.")

    lower = transcript.lower()
    if "agent:" not in lower or "customer:" not in lower:
        flags.append("missing_speaker_turns")
        reasons.append("transcript does not contain recognizable 'Agent:'/'Customer:' turns.")

    injected = _find_first(transcript, PROMPT_INJECTION_PHRASES)
    if injected:
        flags.append("possible_prompt_injection")
        reasons.append(f"Detected a potential prompt-injection phrase: '{injected}'.")

    if stripped and not _find_first(transcript, SALES_RELEVANCE_KEYWORDS):
        flags.append("possible_off_topic")
        reasons.append("No sales-call-relevant keywords detected.")

    passed = not flags
    return CheckResponse(
        passed=passed,
        reason="; ".join(reasons),
        flags=flags,
        safe_text=None,
        human_review_required=False,
        mock=True,
    )


def check_output(payload: OutputCheckRequest) -> CheckResponse:
    flags: list[str] = []
    reasons: list[str] = []

    if payload.historical_claims_present and not payload.citations:
        flags.append("missing_citation")
        reasons.append("historical_claims_present is true but no call_id citations were provided.")

    all_text = " ".join(_collect_strings(payload.final_analysis))
    placeholder_hit = _find_first(all_text, PLACEHOLDER_PATTERNS)
    if placeholder_hit:
        flags.append("unsupported_placeholder_fact")
        reasons.append(f"Detected unsupported placeholder content in final_analysis: '{placeholder_hit}'.")

    human_review_required = payload.confidence < 0.65
    if human_review_required:
        flags.append("low_confidence")
        # Low confidence alone routes to human review; it does not by itself
        # fail the guardrail check (that's the Router's job, CLAUDE.md §2).

    hard_fail_flags = [f for f in flags if f != "low_confidence"]
    passed = not hard_fail_flags

    return CheckResponse(
        passed=passed,
        reason="; ".join(reasons),
        flags=flags,
        safe_text=None,
        human_review_required=human_review_required,
        mock=True,
    )
