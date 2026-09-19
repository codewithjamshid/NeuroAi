"""patients, caregivers, consents, patient_levels, mood_entries, screenings, red_flags (TZ §4.5)."""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin
from app.modules.users.models import JSONType


class StrokeType(StrEnum):
    ISCHEMIC = "ischemic"
    HEMORRHAGIC = "hemorrhagic"
    UNKNOWN = "unknown"


class AphasiaType(StrEnum):
    MOTOR = "motor"
    SENSORY = "sensory"
    GLOBAL = "global"
    AMNESTIC = "amnestic"
    UNKNOWN = "unknown"


class Dialect(StrEnum):
    STANDARD = "standard"
    KHOREZM = "khorezm"
    OTHER = "other"


class ExerciseCategory(StrEnum):
    SPEECH = "speech"
    FACE = "face"
    COGNITIVE = "cognitive"
    HAND = "hand"


class RedFlagCategory(StrEnum):
    SELF_HARM = "self_harm"
    STROKE_SIGNS = "stroke_signs"
    FALL = "fall"
    MEDICATION = "medication"
    ABUSE = "abuse"
    ADHERENCE = "adherence"
    OTHER = "other"


class RedFlagStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Patient(UUIDTimestampMixin, Base):
    __tablename__ = "patients"

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    clinician_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_year: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(String(8))
    stroke_date: Mapped[date | None] = mapped_column()
    stroke_type: Mapped[str | None] = mapped_column(String(16))
    affected_side: Mapped[str | None] = mapped_column(String(8))
    aphasia_type: Mapped[str | None] = mapped_column(String(16))
    dysarthria: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    facial_palsy_side: Mapped[str | None] = mapped_column(String(8))
    dominant_hand: Mapped[str | None] = mapped_column(String(8))
    dialect: Mapped[str] = mapped_column(String(16), nullable=False, default="standard")
    interests: Mapped[list[str] | None] = mapped_column(JSONType)
    family_members: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType)
    habits: Mapped[list[str] | None] = mapped_column(JSONType)
    notes: Mapped[str | None] = mapped_column(Text)
    pin_hash: Mapped[str | None] = mapped_column(String(255))
    consent_id: Mapped[uuid.UUID | None] = mapped_column()


class Caregiver(UUIDTimestampMixin, Base):
    __tablename__ = "caregivers"
    __table_args__ = (UniqueConstraint("user_id", "patient_id", name="uq_caregiver_user_patient"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    relation: Mapped[str | None] = mapped_column(String(32))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Consent(UUIDTimestampMixin, Base):
    __tablename__ = "consents"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    signed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    scopes: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    signed_at: Mapped[datetime] = mapped_column(nullable=False)


class PatientLevel(UUIDTimestampMixin, Base):
    __tablename__ = "patient_levels"
    __table_args__ = (UniqueConstraint("patient_id", "category", name="uq_patient_level_cat"),)

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    locked_by_clinician: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class MoodEntry(UUIDTimestampMixin, Base):
    __tablename__ = "mood_entries"
    __table_args__ = (Index("ix_mood_entries_patient_ts", "patient_id", "ts"),)

    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False)
    ts: Mapped[datetime] = mapped_column(nullable=False)
    self_score: Mapped[int | None] = mapped_column(Integer)
    derived_valence: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="patient")


class Screening(UUIDTimestampMixin, Base):
    __tablename__ = "screenings"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(8), nullable=False)
    answers: Mapped[list[int] | None] = mapped_column(JSONType)
    score: Mapped[int | None] = mapped_column(Integer)
    ts: Mapped[datetime] = mapped_column(nullable=False)
    visible_to: Mapped[str] = mapped_column(String(16), nullable=False, default="clinician")


class RedFlag(UUIDTimestampMixin, Base):
    __tablename__ = "red_flags"
    __table_args__ = (Index("ix_red_flags_patient_status", "patient_id", "status"),)

    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sessions.id"))
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    detector: Mapped[str] = mapped_column(String(16), nullable=False, default="rule")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    notified: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    note: Mapped[str | None] = mapped_column(Text)
