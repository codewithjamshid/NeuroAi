"""Safety outcome handed back to the companion turn (TZ §6)."""

import uuid

from pydantic import BaseModel

from app.modules.companion.schemas import Risk, SuggestedAction


class SafetyOutcome(BaseModel):
    risk: Risk
    flag_id: uuid.UUID | None = None
    flag_created: bool = False
    detector: str = "llm"
    override_text: str | None = None  # replaces reply_text + tts_text when set
    suggested_action: SuggestedAction | None = None
    medication: bool = False
    keyword_hits: list[dict] = []
