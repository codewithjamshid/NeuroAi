import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

FollowUp = Literal["none", "body_map", "yes_no"]


class Candidate(BaseModel):
    key: str
    label: str
    emoji: str | None = None
    p: float = Field(ge=0, le=1)


class InterpreterGuess(BaseModel):
    """LLM response schema (TZ Ilova B)."""

    candidates: list[Candidate]
    board_suggested: bool = False
    spoken_text: str
    family_note: str
    follow_up: FollowUp = "none"


class GuessOut(BaseModel):
    interpretation_id: uuid.UUID
    session_id: uuid.UUID
    raw_transcript: str
    confidence: float
    candidates: list[Candidate]
    board_suggested: bool = False


class ConfirmIn(BaseModel):
    interpretation_id: uuid.UUID
    candidate_key: str | None = None
    custom_text: str | None = Field(default=None, max_length=300)


class ConfirmOut(BaseModel):
    spoken_text: str
    tts_url: str | None = None
    tts_provider: str | None = None
    family_note: str
    follow_up: FollowUp = "none"
    chosen: str


class BoardItem(BaseModel):
    key: str
    label: str
    emoji: str | None = None
    group: str | None = None


class BodyPart(BaseModel):
    key: str
    label: str
    emoji: str | None = None


class BoardOut(BaseModel):
    items: list[BoardItem]
    body_map: list[BodyPart]


class InterpretationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    session_id: uuid.UUID | None = None
    raw_transcript: str | None = None
    stt_confidence: float | None = None
    candidates: list[dict[str, Any]] | None = None
    chosen: str | None = None
    spoken_text: str | None = None
    family_note: str | None = None
    confirmed_by: str | None = None
    created_at: datetime
