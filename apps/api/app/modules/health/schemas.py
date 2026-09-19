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
    """Compact per-provider entry (web StatusPanel); derived from the chain status."""

    name: str
    status: Status
    latency_ms: int | None = None
    circuit: Literal["closed", "open", "half_open"] = "closed"


class ChainProviderStatus(BaseModel):
    """FallbackChain.status() entry (TZ §4.4: online/offline, last latency, circuit)."""

    name: str
    configured: bool = True
    circuit: Literal["closed", "open"] = "closed"
    status: Status = "unknown"
    last_ok: bool | None = None
    last_latency_ms: int | None = None
    last_error: str | None = None


class ChainsStatus(BaseModel):
    llm: list[ChainProviderStatus] = []
    stt: list[ChainProviderStatus] = []
    tts: list[ChainProviderStatus] = []
    voice_emotion: list[ChainProviderStatus] = []


class ProviderCallOut(BaseModel):
    provider: str
    task: str
    latency_ms: int
    ok: bool
    fallback_index: int
    error: str | None = None
    created_at: datetime


class ProvidersHealth(BaseModel):
    worker: WorkerStatus
    llm: list[ProviderStatus] = []
    stt: list[ProviderStatus] = []
    tts: list[ProviderStatus] = []
    voice_emotion: list[ProviderStatus] = []
    chains: ChainsStatus = ChainsStatus()
    recent_calls: list[ProviderCallOut] = []
