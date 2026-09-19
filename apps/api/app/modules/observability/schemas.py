import uuid
from datetime import datetime

from pydantic import BaseModel


class ProviderCallOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: str
    task: str
    latency_ms: int | None = None
    ok: bool
    fallback_index: int
    error: str | None = None
    created_at: datetime
