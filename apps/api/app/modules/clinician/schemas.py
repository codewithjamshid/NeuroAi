import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.patients.schemas import RedFlagOut


class DayMetrics(BaseModel):
    """One calendar day (TZ §8.3). Fractions 0–1 except adherence_* (%), cue 0–3, mood 1–5."""

    date: date
    speech_accuracy: float | None = None
    independence: float | None = None
    avg_cue_level: float | None = None
    fsi: float | None = None
    mood_self: float | None = None
    valence: float | None = None
    adherence_exercise: float | None = None
    adherence_medication: float | None = None


class AdherenceWeek(BaseModel):
    exercise: float | None = None
    medication: float | None = None


class DashboardOut(BaseModel):
    days: list[DayMetrics]
    flags: list[RedFlagOut]
    adherence_week: AdherenceWeek
    sessions_count: int
    fsi_base: float | None = None


class ClinicianPatientOut(BaseModel):
    id: uuid.UUID
    full_name: str
    age: int | None = None
    aphasia_type: str | None = None
    open_flags: int = 0
    last_activity: datetime | None = None
    adherence_week: float | None = None


class ClinicianSessionOut(BaseModel):
    id: uuid.UUID
    mode: str
    started_at: datetime
    ended_at: datetime | None = None
    summary: dict[str, Any] | None = None
    accuracy: float | None = None
    attempts: int = 0
