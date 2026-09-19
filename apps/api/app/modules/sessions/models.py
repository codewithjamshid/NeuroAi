"""sessions, messages, exercise_templates, exercise_attempts, face/hand/voice metrics,
patient_states, interpretations, reports (TZ §4.5)."""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin
from app.modules.users.models import JSONType


class SessionMode(StrEnum):
    COMPANION = "companion"
    EXERCISE = "exercise"
    INTERPRETER = "interpreter"
    CHECKIN = "checkin"


class MessageRole(StrEnum):
    PATIENT = "patient"
    AI = "ai"
    CAREGIVER = "caregiver"
    SYSTEM = "system"


class Modality(StrEnum):
    TEXT = "text"
    VOICE = "voice"
    PICTOGRAM = "pictogram"


class AttemptResult(StrEnum):
    CORRECT = "correct"
    PARTIAL = "partial"
    INCORRECT = "incorrect"
    SKIPPED = "skipped"


class Session(UUIDTimestampMixin, Base):
    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_patient_started", "patient_id", "started_at"),)

    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    device_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column()
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    state_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    mood_self: Mapped[int | None] = mapped_column(Integer)


class Message(UUIDTimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_session_created", "session_id", "created_at"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    modality: Mapped[str] = mapped_column(String(16), nullable=False, default="text")
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    audio_path: Mapped[str | None] = mapped_column(String(255))
    stt_confidence: Mapped[float | None] = mapped_column(Float)
    stt_provider: Mapped[str | None] = mapped_column(String(32))
    llm_meta: Mapped[dict[str, Any] | None] = mapped_column(JSONType)


class ExerciseTemplate(UUIDTimestampMixin, Base):
    __tablename__ = "exercise_templates"
    __table_args__ = (Index("ix_exercise_templates_cat_level", "category", "level"),)

    key: Mapped[str | None] = mapped_column(String(64), unique=True)  # seed natural key
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    subtype: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_tts_path: Mapped[str | None] = mapped_column(String(255))
    stimulus: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    expected: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    cues: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    tags: Mapped[list[str] | None] = mapped_column(JSONType)
    lang: Mapped[str] = mapped_column(String(16), nullable=False, default="uz-Latn")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ExerciseAttempt(UUIDTimestampMixin, Base):
    __tablename__ = "exercise_attempts"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("exercise_templates.id"))
    category: Mapped[str | None] = mapped_column(String(16))
    recognized_text: Mapped[str | None] = mapped_column(Text)
    expected_answer: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    result: Mapped[str | None] = mapped_column(String(16))
    cue_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_ms: Mapped[int | None] = mapped_column(Integer)
    llm_judgement: Mapped[dict[str, Any] | None] = mapped_column(JSONType)


class FaceMetric(UUIDTimestampMixin, Base):
    __tablename__ = "face_metrics"
    __table_args__ = (Index("ix_face_metrics_session_ts", "session_id", "ts"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    ts: Mapped[float] = mapped_column(Float, nullable=False)
    exercise_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("exercise_attempts.id")
    )
    face_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fsi: Mapped[float | None] = mapped_column(Float)
    rest_asym: Mapped[float | None] = mapped_column(Float)
    smile_asym: Mapped[float | None] = mapped_column(Float)
    brow_asym: Mapped[float | None] = mapped_column(Float)
    eye_asym: Mapped[float | None] = mapped_column(Float)
    mouth_open: Mapped[float | None] = mapped_column(Float)
    attention: Mapped[float | None] = mapped_column(Float)
    fatigue_proxy: Mapped[float | None] = mapped_column(Float)
    expr_hint: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    blendshapes_avg: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    reps: Mapped[int | None] = mapped_column(Integer)


class HandMetric(UUIDTimestampMixin, Base):
    __tablename__ = "hand_metrics"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ts: Mapped[float] = mapped_column(Float, nullable=False)
    side: Mapped[str | None] = mapped_column(String(8))
    reps: Mapped[int | None] = mapped_column(Integer)
    open_close_amp: Mapped[float | None] = mapped_column(Float)
    tap_rate: Mapped[float | None] = mapped_column(Float)


class VoiceMetric(UUIDTimestampMixin, Base):
    __tablename__ = "voice_metrics"

    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    arousal: Mapped[float | None] = mapped_column(Float)
    valence: Mapped[float | None] = mapped_column(Float)
    dominance: Mapped[float | None] = mapped_column(Float)
    label: Mapped[str | None] = mapped_column(String(32))
    speech_rate_wps: Mapped[float | None] = mapped_column(Float)
    pause_ratio: Mapped[float | None] = mapped_column(Float)
    provider: Mapped[str | None] = mapped_column(String(32))


class PatientState(UUIDTimestampMixin, Base):
    __tablename__ = "patient_states"
    __table_args__ = (Index("ix_patient_states_session_ts", "session_id", "ts"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    ts: Mapped[datetime] = mapped_column(nullable=False)
    engagement: Mapped[str] = mapped_column(String(8), nullable=False, default="medium")
    fatigue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mood: Mapped[str] = mapped_column(String(8), nullable=False, default="unknown")
    mood_conf: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    distress: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stt_confidence: Mapped[float | None] = mapped_column(Float)
    explain: Mapped[list[str] | None] = mapped_column(JSONType)
    inputs: Mapped[dict[str, Any] | None] = mapped_column(JSONType)


class Interpretation(UUIDTimestampMixin, Base):
    __tablename__ = "interpretations"

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sessions.id", ondelete="SET NULL"), index=True
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("patients.id"), index=True)
    raw_transcript: Mapped[str | None] = mapped_column(Text)
    stt_confidence: Mapped[float | None] = mapped_column(Float)
    candidates: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType)
    chosen: Mapped[str | None] = mapped_column(String(64))
    spoken_text: Mapped[str | None] = mapped_column(Text)
    family_note: Mapped[str | None] = mapped_column(Text)
    confirmed_by: Mapped[str | None] = mapped_column(String(16))


class Report(UUIDTimestampMixin, Base):
    __tablename__ = "reports"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(nullable=False)
    period_end: Mapped[date] = mapped_column(nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    generated_by: Mapped[str | None] = mapped_column(String(64))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
