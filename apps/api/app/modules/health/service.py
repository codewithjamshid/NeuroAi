import asyncio
import logging
import time
from datetime import UTC, datetime
from urllib.parse import urlsplit

from app import APP_NAME, __version__
from app.ai.worker.client import WorkerClientProtocol
from app.core.config import Settings
from app.modules.health.schemas import HealthResponse, ProvidersHealth, WorkerStatus

log = logging.getLogger(__name__)


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


async def get_providers_health(settings: Settings, client: WorkerClientProtocol) -> ProvidersHealth:
    worker = await get_worker_status(client, settings.ai_worker_timeout_s)
    return ProvidersHealth(worker=worker)  # llm/stt/tts/voice_emotion lists: T-04
