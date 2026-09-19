import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Sex = Literal["male", "female"]
Side = Literal["left", "right", "both", "none"]
StrokeTypeL = Literal["ischemic", "hemorrhagic", "unknown"]
AphasiaTypeL = Literal["motor", "sensory", "global", "amnestic", "unknown"]
DialectL = Literal["standard", "khorezm", "other"]
FlagStatus = Literal["open", "acknowledged", "resolved"]


class FamilyMember(BaseModel):
    name: str
    relation: str


class ConsentIn(BaseModel):
    scopes: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0"


class PatientBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    birth_year: int | None = Field(default=None, ge=1900, le=2030)
    sex: Sex | None = None
    stroke_date: date | None = None
    stroke_type: StrokeTypeL | None = None
    affected_side: Side | None = None
    aphasia_type: AphasiaTypeL | None = None
    dysarthria: bool = False
    facial_palsy_side: Side | None = None
    dominant_hand: Literal["left", "right"] | None = None
    dialect: DialectL = "standard"
    interests: list[str] = Field(default_factory=list)
    family_members: list[FamilyMember] = Field(default_factory=list)
    habits: list[str] = Field(default_factory=list)
    notes: str | None = None


class PatientCreate(PatientBase):
    consent: ConsentIn | None = None
    caregiver_relation: str | None = None  # when a caregiver creates the card
    clinician_id: uuid.UUID | None = None  # admin/caregiver may assign; clinician = self


class PatientPatch(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    birth_year: int | None = Field(default=None, ge=1900, le=2030)
    sex: Sex | None = None
    stroke_date: date | None = None
    stroke_type: StrokeTypeL | None = None
    affected_side: Side | None = None
    aphasia_type: AphasiaTypeL | None = None
    dysarthria: bool | None = None
    facial_palsy_side: Side | None = None
    dominant_hand: Literal["left", "right"] | None = None
    dialect: DialectL | None = None
    interests: list[str] | None = None
    family_members: list[FamilyMember] | None = None
    habits: list[str] | None = None
    notes: str | None = None
    clinician_id: uuid.UUID | None = None


class PatientOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID | None
    clinician_id: uuid.UUID | None
    full_name: str
    birth_year: int | None
    sex: str | None
    stroke_date: date | None
    stroke_type: str | None
    affected_side: str | None
    aphasia_type: str | None
    dysarthria: bool
    facial_palsy_side: str | None
    dominant_hand: str | None
    dialect: str
    interests: list[str] | None
    family_members: list[dict[str, Any]] | None
    habits: list[str] | None
    notes: str | None
    consent_id: uuid.UUID | None
    created_at: datetime


class ConsentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    signed_by: uuid.UUID | None
    version: str
    scopes: dict[str, Any]
    signed_at: datetime


class MoodIn(BaseModel):
    self_score: int = Field(ge=1, le=5)


class MoodOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    ts: datetime
    self_score: int | None
    derived_valence: float | None
    source: str


class MoodTrendPoint(BaseModel):
    date: date
    self_score: float | None = None
    valence: float | None = None


class RedFlagOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    session_id: uuid.UUID | None
    category: str
    severity: str
    evidence: str | None
    detector: str
    status: str
    note: str | None
    created_at: datetime


class RedFlagPatch(BaseModel):
    status: FlagStatus
    note: str | None = None
