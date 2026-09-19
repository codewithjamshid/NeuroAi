import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Mode = Literal["companion", "exercise", "interpreter", "checkin"]


class SessionCreate(BaseModel):
    patient_id: uuid.UUID
    mode: Mode


class SessionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    mode: str
    device_user_id: uuid.UUID | None = None
    started_at: datetime
    ended_at: datetime | None = None
    summary: dict[str, Any] | None = None
    mood_self: int | None = None


class SessionSummary(BaseModel):
    caregiver_text: str
    clinician_text: str
    attention_needed: bool = False


class EndOut(BaseModel):
    summary: SessionSummary


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    modality: str
    text: str
    audio_url: str | None = None
    stt_confidence: float | None = None
    stt_provider: str | None = None
    created_at: datetime
    llm_meta: dict[str, Any] | None = None


class TranscriptOut(BaseModel):
    session: SessionOut
    messages: list[MessageOut]


class ExprHint(BaseModel):
    label: str = "neutral"
    conf: float = 0.0


class FaceMetricIn(BaseModel):
    """One batch element (TZ Ilova B); yaw/pitch are accepted and ignored."""

    ts: float
    face_present: bool = True
    fsi: float | None = None
    rest_asym: float | None = None
    smile_asym: float | None = None
    brow_asym: float | None = None
    eye_asym: float | None = None
    mouth_open: float | None = None
    attention: float | None = None
    fatigue_proxy: float | None = None
    expr_hint: ExprHint | None = None
    blendshapes_avg: dict[str, float] | None = None
    reps: int | None = None
    exercise_attempt_id: uuid.UUID | None = None


class StoredOut(BaseModel):
    stored: int


class PatientStateIn(BaseModel):
    """`PatientState` (TZ Ilova B) — computed by code, posted by the companion/fusion layer."""

    engagement: Literal["low", "medium", "high"] = "medium"
    fatigue: float = Field(default=0.0, ge=0, le=1)
    mood: Literal["negative", "neutral", "positive", "unknown"] = "unknown"
    mood_conf: float = Field(default=0.0, ge=0, le=1)
    distress: bool = False
    stt_confidence: float | None = None
    explain: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)


class PatientStateOut(PatientStateIn):
    ts: datetime | None = None
