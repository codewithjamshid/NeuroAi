import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Kind = Literal["exercise", "medication", "checkin"]
Category = Literal["speech", "face", "cognitive", "hand", "mood"]
ProtocolStatusL = Literal["active", "paused", "done"]
MedLogStatusL = Literal["taken", "missed", "unknown"]


class Frequency(BaseModel):
    times_per_day: int = Field(default=1, ge=1, le=10)
    days: list[int] | None = None  # isoweekday 1..7; None → every day
    times: list[str] | None = None  # ["09:00", "21:00"]


class TemplateItem(BaseModel):
    kind: Kind = "exercise"
    title: str | None = None
    category: Category | None = None
    level: int | None = Field(default=None, ge=1, le=5)
    frequency: Frequency = Field(default_factory=Frequency)
    duration_min: int | None = None
    params: dict[str, Any] | None = None


class TemplateOut(BaseModel):
    key: str
    title: str
    description: str = ""
    items: list[TemplateItem] = Field(default_factory=list)


class ItemIn(BaseModel):
    kind: Kind = "exercise"
    title: str | None = None
    category: Category | None = None
    level: int | None = Field(default=None, ge=1, le=5)
    frequency: Frequency = Field(default_factory=Frequency)
    duration_min: int | None = None
    params: dict[str, Any] | None = None
    medication_id: uuid.UUID | None = None


class ItemPatch(BaseModel):
    kind: Kind | None = None
    title: str | None = None
    category: Category | None = None
    level: int | None = Field(default=None, ge=1, le=5)
    frequency: Frequency | None = None
    duration_min: int | None = None
    params: dict[str, Any] | None = None
    medication_id: uuid.UUID | None = None


class ItemOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    protocol_id: uuid.UUID
    kind: str
    title: str | None = None
    category: str | None
    level: int | None
    frequency: dict[str, Any] | None
    duration_min: int | None
    params: dict[str, Any] | None
    medication_id: uuid.UUID | None


class ProtocolCreate(BaseModel):
    template_key: str | None = None
    title: str | None = None
    items: list[ItemIn] | None = None
    start_date: date | None = None
    notes: str | None = None


class ProtocolPatch(BaseModel):
    title: str | None = None
    status: ProtocolStatusL | None = None
    notes: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProtocolOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    clinician_id: uuid.UUID | None
    title: str
    template_key: str | None
    status: str
    start_date: date
    end_date: date | None
    notes: str | None
    items: list[ItemOut]
    created_at: datetime


class MedicationIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dose: str | None = None
    schedule: dict[str, Any] = Field(default_factory=lambda: {"times": ["09:00"]})
    notes: str | None = None
    active: bool = True


class MedicationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    dose: str | None
    schedule: dict[str, Any] | None
    notes: str | None
    active: bool


class MedLogIn(BaseModel):
    status: MedLogStatusL
    scheduled_at: datetime | None = None
    taken_at: datetime | None = None


class MedLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    medication_id: uuid.UUID
    scheduled_at: datetime
    taken_at: datetime | None
    status: str
    source: str


class TodayItem(BaseModel):
    id: str
    kind: Kind
    title: str
    category: str | None = None
    level: int | None = None
    duration_min: int | None = None
    time: str | None = None
    done: bool = False
    protocol_item_id: uuid.UUID | None = None
    medication_id: uuid.UUID | None = None


class TodayOut(BaseModel):
    date: date
    items: list[TodayItem]
    mood_self: int | None = None
