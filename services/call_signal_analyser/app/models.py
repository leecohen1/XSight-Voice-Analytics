"""Pydantic request/response models for the Call Signal Analyser.

Enums and numeric ranges match docs/dataset_design.md §5-§11. Phase 6 accepts
JSON input only (audio_features and structured_fields as pre-computed
numbers/labels) — real audio file upload and PyTorch inference are Phase 13.

Ground Truth Rule (CLAUDE.md): audio-derived features that could not be
measured (e.g. no audio file available, or a feature the lightweight
preprocessing couldn't compute) must be representable as missing — never
silently defaulted to a fabricated number such as `silence_ratio: 0.0`. Every
field of `AudioFeatures` is therefore `Optional`, defaulting to `None` when
not provided. When a value IS provided, the existing range validation still
applies — partial evidence is fine, fabricated evidence is not.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

CustomerIntent = Literal["high", "medium", "low", "unclear"]
MainObjection = Literal[
    "price", "timing", "trust", "competitor", "no_need",
    "authority", "integration", "security", "other", "none",
]
CustomerSentiment = Literal["positive", "neutral", "negative", "mixed"]
ClosingAttempt = Literal["strong", "medium", "weak", "none"]
EnergyLevel = Literal["low", "medium", "high"]
RiskLevel = Literal["Low", "Medium", "High"]
PredictedOutcome = Literal["Sale", "No Sale", "Follow-up Needed"]


class AudioFeatures(BaseModel):
    call_duration_seconds: Optional[int] = Field(None, ge=180, le=900)
    silence_ratio: Optional[float] = Field(None, ge=0.05, le=0.35)
    speaking_rate_wpm: Optional[int] = Field(None, ge=100, le=190)
    speech_to_non_speech_ratio: Optional[float] = Field(None, ge=0.65, le=0.95)
    agent_talk_ratio: Optional[float] = Field(None, ge=0.35, le=0.75)
    average_energy_level: Optional[EnergyLevel] = None


class StructuredFields(BaseModel):
    customer_intent: CustomerIntent
    main_objection: MainObjection
    customer_sentiment: CustomerSentiment
    closing_attempt: ClosingAttempt
    decision_maker_present: bool


class AnalyseCallRequest(BaseModel):
    transcript: str = Field(..., min_length=20)
    audio_features: AudioFeatures
    structured_fields: StructuredFields


class AnalyseCallResponse(BaseModel):
    predicted_outcome: PredictedOutcome
    lead_quality_score: int = Field(..., ge=1, le=5)
    agent_performance_score: int = Field(..., ge=1, le=5)
    risk_level: RiskLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    detected_signals: list[str]
    human_review_required: bool
    mock: bool
    # Additive, Phase-6.1 (demo-day uncertainty pass): names of AudioFeatures
    # fields that were missing (None) on this request. Empty list means every
    # scored audio feature was present. See app/mock_rules.py for how missing
    # features affect confidence and human_review_required.
    missing_features: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
