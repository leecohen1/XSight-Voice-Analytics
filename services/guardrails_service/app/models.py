"""Pydantic request/response models for the Guardrails Service.

POST /check/input uses a discriminated union on `stage` (`pre_transcription`
vs `post_transcription`), matching the two-stage design in CLAUDE.md §5 —
one endpoint, stage-aware validation, rather than two separate endpoints.
"""
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class FileMetadata(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int = Field(..., ge=0)
    duration_seconds: Optional[float] = Field(default=None, ge=0)


class SubmissionMetadata(BaseModel):
    agent_name: Optional[str] = None
    call_date: Optional[str] = None


class PreTranscriptionInput(BaseModel):
    stage: Literal["pre_transcription"]
    file_metadata: FileMetadata
    submission_metadata: SubmissionMetadata = Field(default_factory=SubmissionMetadata)


class PostTranscriptionInput(BaseModel):
    stage: Literal["post_transcription"]
    transcript: str = ""
    submission_metadata: SubmissionMetadata = Field(default_factory=SubmissionMetadata)


CheckInputRequest = Annotated[
    Union[PreTranscriptionInput, PostTranscriptionInput],
    Field(discriminator="stage"),
]


class OutputCheckRequest(BaseModel):
    final_analysis: dict = Field(default_factory=dict)
    citations: list[str] = Field(default_factory=list)
    historical_claims_present: bool = False
    confidence: float = Field(..., ge=0.0, le=1.0)


class CheckResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    passed: bool = Field(alias="pass")
    reason: str
    flags: list[str]
    safe_text: Optional[str] = None
    human_review_required: bool
    mock: bool


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
