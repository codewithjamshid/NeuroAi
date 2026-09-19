import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.sessions.schemas import PatientStateOut


class InterpretationBrief(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    raw_transcript: str | None = None
    chosen: str | None = None
    spoken_text: str | None = None
    family_note: str | None = None
    created_at: datetime


class CaregiverTodayOut(BaseModel):
    state: PatientStateOut | None = None
    mood_self: int | None = None
    exercises_done: int = 0
    exercises_planned: int = 0
    last_interpretations: list[InterpretationBrief] = Field(default_factory=list)
    flags_open: int = 0
    tips_cached: list[str] | None = None


class Tips(BaseModel):
    """LLM response schema (Ilova A.7)."""

    tips: list[str] = Field(default_factory=list)


class TipsOut(BaseModel):
    tips: list[str]
