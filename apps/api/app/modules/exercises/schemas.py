import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

NextAction = Literal["next_item", "retry_with_cue", "suggest_break"]


class NextCue(BaseModel):
    level: int = Field(ge=1, le=3)
    text: str


class CoachVerdict(BaseModel):
    """LLM judge response schema (TZ Ilova B)."""

    result: Literal["correct", "partial", "incorrect"]
    feedback_text: str
    tts_text: str
    next_action: NextAction
    next_cue: NextCue | None = None
    note_for_clinician: str = ""


class TemplateOut(BaseModel):
    id: uuid.UUID
    key: str | None = None
    category: str
    subtype: str
    level: int
    prompt_text: str
    prompt_tts_url: str | None = None
    stimulus: dict[str, Any] | None = None
    cues: dict[str, Any] | None = None


class Progress(BaseModel):
    index: int  # 1-based position of the current item
    total: int


class NextOut(BaseModel):
    done: bool = False
    attempt_id: uuid.UUID | None = None
    template: TemplateOut | None = None
    cue_level: int = 0
    progress: Progress | None = None
    summary: dict[str, Any] | None = None


class NextCueOut(NextCue):
    tts_url: str | None = None


class SubmitOut(BaseModel):
    score: float
    result: str
    recognized_text: str | None = None
    feedback_text: str
    tts_url: str | None = None
    tts_provider: str | None = None
    next_action: NextAction
    next_cue: NextCueOut | None = None


class OkOut(BaseModel):
    ok: bool = True


class FaceSummary(BaseModel):
    reps: int = Field(ge=0)
    target_reps: int = Field(default=5, ge=1)
    mean_amplitude: float = Field(default=0.0, ge=0, le=1)
    fsi: float = Field(default=0.0, ge=0, le=1)


class ExerciseTemplateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    key: str | None = None
    category: str
    subtype: str
    level: int
    prompt_text: str
    stimulus: dict[str, Any] | None = None
    expected: dict[str, Any] | None = None
    cues: dict[str, Any] | None = None
    tags: list[str] | None = None
    active: bool = True
