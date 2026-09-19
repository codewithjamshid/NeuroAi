from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Status = Literal["online", "offline", "unknown"]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    app: str
    version: str
    env: str
    time: datetime


class WorkerStatus(BaseModel):
    mode: Literal["mock", "http"]
    url: str
    status: Status
    latency_ms: int | None = None
    models: dict[str, str] = {}


class ProviderStatus(BaseModel):
    """Per-provider entry, filled by FallbackChain in T-04 (TZ §4.4)."""

    name: str
    status: Status
    latency_ms: int | None = None
    circuit: Literal["closed", "open", "half_open"] = "closed"


class ProvidersHealth(BaseModel):
    worker: WorkerStatus
    llm: list[ProviderStatus] = []
    stt: list[ProviderStatus] = []
    tts: list[ProviderStatus] = []
    voice_emotion: list[ProviderStatus] = []
