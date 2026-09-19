import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class LinkOut(BaseModel):
    code: str
    bot_username: str | None = None
    expires_in_s: int = 900


class LinkStatusOut(BaseModel):
    linked: bool
    chat_id_masked: str | None = None


class NotificationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    channel: str
    kind: str
    payload: dict[str, Any] | None = None
    status: str
    sent_at: datetime | None = None
    created_at: datetime
