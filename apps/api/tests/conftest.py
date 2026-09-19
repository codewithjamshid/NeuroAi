from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AI_WORKER_URL", "mock")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    # `make test` exports the demo .env (cloud-first chains, real worker URL, model overrides);
    # tests assume the TZ defaults, so pin them here (process env wins over .env files).
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("LLM_PROVIDERS", "gemini,openai")
    monkeypatch.setenv("STT_PROVIDERS", "worker,gemini,openai")
    monkeypatch.setenv("TTS_PROVIDERS", "worker,openai,browser")
    monkeypatch.setenv("VOICE_EMOTION_PROVIDERS", "worker")
    monkeypatch.setenv("GEMINI_MODEL_FAST", "gemini-2.5-flash")
    monkeypatch.setenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    get_settings.cache_clear()


@pytest.fixture
def app() -> FastAPI:
    from app.main import create_app

    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
