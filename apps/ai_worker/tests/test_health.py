import logging

import pytest
from httpx import AsyncClient

from app import __version__, models, stt
from app.config import get_settings
from app.errors import ModelUnavailable
from app.stt import logprob_to_confidence


@pytest.fixture
def reset_registry():
    yield
    models.unload_all()


async def test_health_is_public_and_all_models_disabled_on_laptop(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body == {
        "models": {
            "stt": "disabled",
            "tts": "disabled",
            "voice_emotion": "disabled",
            "medllm": "disabled",
        },
        "gpu": None,
        "version": __version__,
    }


async def test_enabled_but_unavailable_model_is_disabled(
    monkeypatch: pytest.MonkeyPatch, caplog, client: AsyncClient, reset_registry
) -> None:
    """Library missing on this machine (ModelUnavailable) → "disabled" + warning, not "error"."""

    def unavailable(_settings) -> None:
        raise ModelUnavailable("faster-whisper is not installed (test)")

    monkeypatch.setattr(stt, "load", unavailable)
    monkeypatch.setenv("MODELS_ENABLED", "stt,unknown_model")
    get_settings.cache_clear()
    with caplog.at_level(logging.WARNING, logger="ai_worker.models"):
        statuses = models.load_enabled(get_settings())
    assert statuses["stt"] == "disabled"
    assert statuses["tts"] == "disabled"
    assert any("stt unavailable" in m for m in caplog.messages)
    assert any("unknown_model" in m for m in caplog.messages)

    r = await client.get("/health")
    assert r.json()["models"]["stt"] == "disabled"


async def test_enabled_model_with_real_load_failure_reports_error(
    monkeypatch: pytest.MonkeyPatch, caplog, client: AsyncClient, reset_registry
) -> None:
    """Library present but load() blows up (model dir missing, CUDA error) → "error"."""

    def broken(_settings) -> None:
        raise RuntimeError("CUDA out of memory (test)")

    monkeypatch.setattr(stt, "load", broken)
    monkeypatch.setenv("MODELS_ENABLED", "stt")
    get_settings.cache_clear()
    with caplog.at_level(logging.ERROR, logger="ai_worker.models"):
        statuses = models.load_enabled(get_settings())
    assert statuses["stt"] == "error"
    assert statuses["tts"] == "disabled"
    assert any("stt failed to load" in m for m in caplog.messages)

    r = await client.get("/health")
    assert r.json()["models"]["stt"] == "error"

    models.unload_all()
    assert models.statuses()["stt"] == "disabled"


async def test_loaded_model_reports_loaded(
    monkeypatch: pytest.MonkeyPatch, client: AsyncClient, reset_registry
) -> None:
    monkeypatch.setattr(stt, "load", lambda _settings: setattr(stt, "_model", object()))
    monkeypatch.setenv("MODELS_ENABLED", "stt")
    get_settings.cache_clear()
    assert models.load_enabled(get_settings())["stt"] == "loaded"
    r = await client.get("/health")
    assert r.json()["models"]["stt"] == "loaded"


def test_logprob_to_confidence_is_clamped() -> None:
    assert logprob_to_confidence(0.0) == 1.0
    assert 0.0 < logprob_to_confidence(-0.5) < 1.0
    assert logprob_to_confidence(-50.0) < 1e-9
    assert logprob_to_confidence(5.0) == 1.0  # clamped upper bound
    assert logprob_to_confidence(-1.0) < logprob_to_confidence(-0.1)
