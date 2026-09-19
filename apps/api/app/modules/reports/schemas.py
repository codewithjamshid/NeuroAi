import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel

Period = Literal["7d", "14d"]


class WeeklyReport(BaseModel):
    """LLM response schema (Ilova A.6 outputs markdown; wrapped in JSON for structured output)."""

    content_md: str


class ReportOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    content_md: str
    metrics: dict[str, Any] | None = None
    generated_by: str | None = None
    period_start: date
    period_end: date
    created_at: datetime
