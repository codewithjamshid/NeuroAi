import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from app import APP_NAME, __version__
from app.ai.chains import get_chains, recent_calls
from app.ai.worker.client import WorkerClientProtocol
from app.core.config import Settings
from app.modules.health.schemas import (
    ChainsStatus,
    HealthResponse,
    ProviderCallOut,
    ProvidersHealth,
    ProviderStatus,
    WorkerStatus,
)

log = logging.getLogger(__name__)

RECENT_CALLS_LIMIT = 20


def get_health(settings: Settings) -> HealthResponse:
    return HealthResponse(
        app=APP_NAME, version=__version__, env=settings.app_env, time=datetime.now(UTC)
    )


def mask_url(url: str) -> str:
    """`https://abc-123.ngrok-free.app` → `https://***.ngrok-free.app` (hide the tunnel id)."""
    parts = urlsplit(url)
    host = parts.hostname or ""
    labels = host.split(".")
    masked = "***." + ".".join(labels[-2:]) if len(labels) > 2 else host[:2] + "***"
    port = f":{parts.port}" if parts.port else ""
    return f"{parts.scheme}://{masked}{port}"


async def get_worker_status(client: WorkerClientProtocol, timeout_s: float) -> WorkerStatus:
    url = client.base_url if client.mode == "mock" else mask_url(client.base_url)
    started = time.perf_counter()
    try:
        health = await asyncio.wait_for(client.health(), timeout=timeout_s)
    except Exception as exc:
        log.warning("worker health failed", extra={"error": type(exc).__name__})
        return WorkerStatus(mode=client.mode, url=url, status="offline")
    latency_ms = int((time.perf_counter() - started) * 1000)
    return WorkerStatus(
        mode=client.mode, url=url, status="online", latency_ms=latency_ms, models=health.models
    )


def _compact(entries: list[dict[str, Any]]) -> list[ProviderStatus]:
    return [
        ProviderStatus(
            name=e["name"],
            status=e["status"],
            latency_ms=e["last_latency_ms"],
            circuit=e["circuit"],
        )
        for e in entries
    ]


async def get_providers_health(settings: Settings, client: WorkerClientProtocol) -> ProvidersHealth:
    worker = await get_worker_status(client, settings.ai_worker_timeout_s)
    status = get_chains(settings, client).status()
    return ProvidersHealth(
        worker=worker,
        llm=_compact(status["llm"]),
        stt=_compact(status["stt"]),
        tts=_compact(status["tts"]),
        voice_emotion=_compact(status["voice_emotion"]),
        chains=ChainsStatus.model_validate(status),
        recent_calls=[
            ProviderCallOut.model_validate(r.to_dict()) for r in recent_calls(RECENT_CALLS_LIMIT)
        ],
    )
