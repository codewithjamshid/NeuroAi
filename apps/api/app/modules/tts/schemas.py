from pydantic import BaseModel, Field

TEXT_MAX_CHARS = 600


class TTSIn(BaseModel):
    text: str = Field(max_length=TEXT_MAX_CHARS)  # blank → 400 empty_input (service)
    speed: float | None = Field(default=None, ge=0.5, le=2.0)  # None → settings.tts_speed


class TTSOut(BaseModel):
    tts_url: str | None  # "/api/v1/media/tts/<sha1>.wav"; null → client uses speechSynthesis
    provider: str  # "worker" | "openai" | … | "browser" (no audio)
