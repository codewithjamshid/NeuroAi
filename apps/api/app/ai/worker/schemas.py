"""Result shapes of the AI worker API (TZ §4.7); shared by the HTTP client and the mock."""

from typing import Any

from pydantic import BaseModel, Field


class STTSegment(BaseModel):
    start: float
    end: float
    text: str
    avg_logprob: float | None = None


class STTResult(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    segments: list[STTSegment] = []
    latency_ms: int
    provider: str = "worker"


class TTSResult(BaseModel):
    audio_wav: bytes
    latency_ms: int
    provider: str = "worker"


class VoiceEmotionResult(BaseModel):
    label: str
    scores: dict[str, float] = {}
    arousal: float
    valence: float
    dominance: float
    latency_ms: int
    provider: str = "worker"


class WorkerHealth(BaseModel):
    models: dict[str, str]
    gpu: dict[str, Any] | None = None
