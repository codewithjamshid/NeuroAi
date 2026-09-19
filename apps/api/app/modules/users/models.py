"""users, clinics, audit_logs, notifications, provider_calls (TZ §4.5).

Enum-like columns are plain `String` + Python `StrEnum` (no native PG enums → sqlite parity).
`JSONType` is shared by every module's models (JSONB on Postgres, JSON elsewhere).
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin

JSONType = JSON().with_variant(JSONB(), "postgresql")


class Role(StrEnum):
    PATIENT = "patient"
    CAREGIVER = "caregiver"
    CLINICIAN = "clinician"
    ADMIN = "admin"


class NotificationChannel(StrEnum):
    TELEGRAM = "telegram"
    PUSH = "push"
    INAPP = "inapp"


class User(UUIDTimestampMixin, Base):
    __tablename__ = "users"

    role: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="uz-Latn")
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    clinic_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clinics.id"))


class Clinic(UUIDTimestampMixin, Base):
    __tablename__ = "clinics"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100))


class AuditLog(UUIDTimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column()
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONType)


class Notification(UUIDTimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    sent_at: Mapped[datetime | None] = mapped_column()


class ProviderCall(UUIDTimestampMixin, Base):
    __tablename__ = "provider_calls"

    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    task: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fallback_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text)
