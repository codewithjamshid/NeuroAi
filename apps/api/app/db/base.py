"""Declarative base + mixin: every table has `id` (uuid), `created_at`, `updated_at` (TZ §9.3).

`sqlalchemy.Uuid` is native UUID on Postgres and CHAR(32) on SQLite, so models work on both.
T-02 models: `class Patient(UUIDTimestampMixin, Base): __tablename__ = "patients"`.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    type_annotation_map = {uuid.UUID: Uuid(), datetime: DateTime(timezone=True)}


class UUIDTimestampMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )
