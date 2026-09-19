"""GET /api/v1/health/providers: chains + recent_calls (T-04); compact lists kept for the web."""

from collections.abc import Iterator

import pytest
from httpx import AsyncClient

from app.ai.chains import get_chains, reset_chains
from app.core.config import get_settings

CHAIN_ENTRY_KEYS = {
    "name",
    "configured",
    "circuit",
    "status",
    "last_ok",
    "last_latency_ms",
    "last_error",
}


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Pin the TZ default chain order: the root .env may put cloud providers first for the demo.
    monkeypatch.setenv("LLM_PROVIDERS", "gemini,openai")
    monkeypatch.setenv("STT_PROVIDERS", "worker,gemini,openai")
    monkeypatch.setenv("TTS_PROVIDERS", "worker,openai,browser")
    monkeypatch.setenv("VOICE_EMOTION_PROVIDERS", "worker")
    get_settings.cache_clear()
    reset_chains()
    yield
    reset_chains()
    get_settings.cache_clear()


async def test_health_providers_shows_chains(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["worker"]["mode"] == "mock" and body["worker"]["status"] == "online"
    chains = body["chains"]
    assert set(chains) == {"llm", "stt", "tts", "voice_emotion"}
    assert chains["stt"][0]["name"] == "worker_mock"
    assert chains["stt"][0]["configured"] is True and chains["stt"][0]["circuit"] == "closed"
    assert chains["tts"][-1]["name"] == "browser"
    assert chains["voice_emotion"][0]["name"] == "worker_mock"
    assert any(e["configured"] for e in chains["llm"])  # a usable LLM always exists (mock)
    for task in chains:
        for entry in chains[task]:
            assert set(entry) == CHAIN_ENTRY_KEYS
    # Compact lists (web StatusPanel) mirror the chains.
    for task in ("llm", "stt", "tts", "voice_emotion"):
        assert [e["name"] for e in body[task]] == [e["name"] for e in chains[task]]
        for entry in body[task]:
            assert set(entry) == {"name", "status", "latency_ms", "circuit"}
    assert body["recent_calls"] == []


async def test_health_providers_recent_calls_after_chain_use(client: AsyncClient) -> None:
    chains = get_chains(get_settings())
    await chains.stt.call("transcribe", b"RIFF", lang="uz")
    await chains.tts.call("synthesize", "Salom")
    body = (await client.get("/api/v1/health/providers")).json()
    stt = body["chains"]["stt"][0]
    assert stt["status"] == "online" and stt["last_ok"] is True and stt["last_latency_ms"] >= 0
    assert body["stt"][0]["status"] == "online"
    calls = body["recent_calls"]
    assert [c["task"] for c in calls] == ["tts", "stt"]  # newest first
    assert calls[1]["provider"] == "worker_mock" and calls[1]["ok"] is True
    assert calls[1]["fallback_index"] == 0 and calls[1]["error"] is None
    assert "created_at" in calls[1]
