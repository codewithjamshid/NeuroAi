"""protocols, protocol_items, medications, medication_logs (TZ §4.5, M6)."""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDTimestampMixin
from app.modules.users.models import JSONType


class ProtocolStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DONE = "done"


class ItemKind(StrEnum):
    EXERCISE = "exercise"
    MEDICATION = "medication"
    CHECKIN = "checkin"


class MedLogStatus(StrEnum):
    TAKEN = "taken"
    MISSED = "missed"
    UNKNOWN = "unknown"


class Protocol(UUIDTimestampMixin, Base):
    __tablename__ = "protocols"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    clinician_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    template_key: Mapped[str | None] = mapped_column(String(64))
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["ProtocolItem"]] = relationship(
        back_populates="protocol",
        cascade="all, delete-orphan",
        order_by="ProtocolItem.created_at",
        lazy="selectin",
    )


class ProtocolItem(UUIDTimestampMixin, Base):
    __tablename__ = "protocol_items"

    protocol_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str | None] = mapped_column(String(16))
    level: Mapped[int | None] = mapped_column(Integer)
    frequency: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    duration_min: Mapped[int | None] = mapped_column(Integer)
    params: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    medication_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("medications.id"))

    protocol: Mapped[Protocol] = relationship(back_populates="items")

    @property
    def title(self) -> str | None:
        return (self.params or {}).get("title")


class Medication(UUIDTimestampMixin, Base):
    __tablename__ = "medications"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dose: Mapped[str | None] = mapped_column(String(100))
    schedule: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class MedicationLog(UUIDTimestampMixin, Base):
    __tablename__ = "medication_logs"

    medication_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medications.id"), nullable=False, index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(nullable=False)
    taken_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="patient")
