"""Reports tests: sqlite + demo seed, LLM chain forced to MockLLM (no network)."""

from collections.abc import Iterator

import pytest
from core.conftest import actors, db_ready, seeded  # noqa: F401

from app.ai.chains import reset_chains
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("LLM_PROVIDERS", "mock")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    reset_chains()
    yield
    reset_chains()
