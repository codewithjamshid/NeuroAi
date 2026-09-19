"""Ilova B: Candidate / Risk / CompanionReply (LLM response_schema) + message endpoint shapes."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.sessions.schemas import PatientStateOut

RiskLevel = Literal["none", "low", "medium", "high"]
RiskCategory = Literal[
    "self_harm", "stroke_signs", "fall", "medication", "abuse", "adherence", "none"
]
SuggestedAction = Literal[
    "none", "offer_break", "start_exercise", "notify_caregiver", "notify_clinician", "body_map"
]


class Candidate(BaseModel):
    key: str
    label: str
    emoji: str | None = None
    p: float = Field(ge=0, le=1)


class Risk(BaseModel):
    level: RiskLevel = "none"
    category: RiskCategory = "none"
    evidence: str = ""


class CompanionReply(BaseModel):
    reply_text: str
    tts_text: str
    intent: str
    needs_confirmation: bool = False
    candidates: list[Candidate] = []
    mood_estimate: Literal["negative", "neutral", "positive", "unknown"] = "unknown"
    suggested_action: SuggestedAction = "none"
    risk: Risk = Risk()


class PatientMessageOut(BaseModel):
    text: str
    stt_confidence: float | None = None
    provider: str | None = None


class AiMessageOut(BaseModel):
    text: str
    tts_url: str | None = None
    tts_provider: str = "browser"


class MessageResponse(BaseModel):
    patient_message: PatientMessageOut
    ai_message: AiMessageOut
    needs_confirmation: bool = False
    candidates: list[Candidate] = []
    state: PatientStateOut
    risk: Risk
    suggested_action: SuggestedAction = "none"
    meta: dict[str, Any] | None = None


class ConfirmIn(BaseModel):
    candidate_key: str = Field(min_length=1, max_length=64)
