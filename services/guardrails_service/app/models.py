"""Pydantic request/response models for the Guardrails Service.

First real (non-mock) implementation of POST /check/input, covering the
pre-transcription stage only. Every request field is optional at the
schema level — presence and validity are enforced by the deterministic
checks in app/guardrails.py, not by Pydantic type constraints, so a
missing/invalid *value* (e.g. no filename) is reported as a normal
`pass: false` result rather than a 422. Only genuinely malformed
requests (wrong JSON types, fields exceeding the length limits below)
are schema-level 422s.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FileMetadata(BaseModel):
    filename: Optional[str] = Field(default=None, max_length=255)
    mime_type: Optional[str] = Field(default=None, max_length=100)
    file_size: Optional[float] = None
    # Backward-compatible alias for older callers (e.g. the current n8n
    # workflow) that still send `size_bytes`. Normalized into `file_size`
    # below — app/guardrails.py reads only `file_size` and never sees this
    # field, so there is exactly one code path for the size check.
    size_bytes: Optional[float] = None
    duration_seconds: Optional[float] = None

    @model_validator(mode="after")
    def _normalize_file_size_alias(self) -> "FileMetadata":
        if self.file_size is None and self.size_bytes is not None:
            self.file_size = self.size_bytes
        return self


class SubmissionMetadata(BaseModel):
    agent_name: Optional[str] = Field(default=None, max_length=200)
    call_date: Optional[str] = Field(default=None, max_length=50)
    customer_name: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=5000)


class CheckInputRequest(BaseModel):
    stage: Optional[str] = Field(default=None, max_length=50)
    file_metadata: FileMetadata = Field(default_factory=FileMetadata)
    submission_metadata: SubmissionMetadata = Field(default_factory=SubmissionMetadata)


class Checks(BaseModel):
    stage_valid: bool
    file_present: bool
    mime_type_allowed: bool
    file_size_allowed: bool
    metadata_valid: bool
    prompt_injection_detected: bool


class CheckInputResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    passed: bool = Field(alias="pass")
    stage: str
    checks: Checks
    reasons: list[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
