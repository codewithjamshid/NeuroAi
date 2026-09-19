"""WorkerClient wire format (TZ §4.7) against an in-memory httpx transport — no network."""

import json
from collections.abc import AsyncIterator

import httpx
import pytest

from app.ai.worker.client import WorkerClient
from app.ai.worker.mock import silence_wav


def _fake_worker(request: httpx.Request) -> httpx.Response:
    assert request.headers["X-Worker-Key"] == "k"
    assert request.headers["ngrok-skip-browser-warning"] == "1"
    if request.url.path == "/health":
        return httpx.Response(200, json={"models": {"stt": "loaded"}, "gpu": {"name": "T4"}})
    if request.url.path == "/stt":
        assert request.url.params["lang"] == "uz"
        assert request.url.params["initial_prompt"] == "suv"
        assert request.headers["content-type"].startswith("multipart/form-data")
        assert b'name="audio"' in request.content and b"RIFF" in request.content
        return httpx.Response(
            200,
            json={
                "text": "suv",
                "confidence": 0.8,
                "segments": [{"start": 0, "end": 0.5, "text": "suv", "avg_logprob": -0.3}],
                "latency_ms": 120,
            },
        )
    if request.url.path == "/tts":
        assert json.loads(request.content) == {"text": "Salom", "speed": 0.85, "style": "neutral"}
        return httpx.Response(200, content=silence_wav(0.1), headers={"content-type": "audio/wav"})
    if request.url.path == "/voice-emotion":
        body = {"label": "sad", "scores": {"sad": 0.7}, "arousal": -0.2, "valence": -0.5}
        return httpx.Response(200, json={**body, "dominance": -0.1})
    return httpx.Response(404)


@pytest.fixture
async def worker() -> AsyncIterator[WorkerClient]:
    transport = httpx.MockTransport(_fake_worker)
    client = WorkerClient(base_url="https://w.example", key="k", timeout_s=2, transport=transport)
    yield client
    await client.aclose()


async def test_health(worker: WorkerClient) -> None:
    health = await worker.health()
    assert health.models == {"stt": "loaded"}
    assert health.gpu == {"name": "T4"}


async def test_stt(worker: WorkerClient) -> None:
    result = await worker.stt(silence_wav(0.1), initial_prompt="suv")
    assert result.text == "suv" and result.confidence == 0.8
    assert result.latency_ms == 120 and result.provider == "worker"
    assert result.segments[0].avg_logprob == -0.3


async def test_tts(worker: WorkerClient) -> None:
    result = await worker.tts("Salom")
    assert result.audio_wav.startswith(b"RIFF") and result.provider == "worker"


async def test_voice_emotion(worker: WorkerClient) -> None:
    result = await worker.voice_emotion(silence_wav(0.1))
    assert result.label == "sad" and result.valence == -0.5
    assert result.latency_ms >= 0  # filled client-side when the worker omits it


async def test_http_error_raises() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(503))
    client = WorkerClient(base_url="https://w.example", key="k", transport=transport)
    with pytest.raises(httpx.HTTPStatusError):
        await client.health()
    await client.aclose()
