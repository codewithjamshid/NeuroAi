"""Request/response shapes — exactly TZ §4.7."""

from typing import Literal

from pydantic import BaseModel, Field

ModelStatus = Literal["loaded", "disabled", "error"]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class STTSegment(BaseModel):
    start: float
    end: float
    text: str
    avg_logprob: float


class STTResponse(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    segments: list[STTSegment]
    latency_ms: int


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    speed: float = Field(default=0.85, gt=0.3, lt=2.0)
    style: str = "neutral"


class VoiceEmotionResponse(BaseModel):
    label: str
    scores: dict[str, float]
    arousal: float
    valence: float
    dominance: float
    latency_ms: int


class MedLLMRequest(BaseModel):
    text: str | None = None
    image_b64: str | None = None
    task: Literal["discharge_summary", "imaging"] = "discharge_summary"


class MedLLMResponse(BaseModel):
    summary_md: str


class GPUInfo(BaseModel):
    name: str
    mem_used_mb: int


class HealthResponse(BaseModel):
    models: dict[str, ModelStatus]
    gpu: GPUInfo | None
    version: str
