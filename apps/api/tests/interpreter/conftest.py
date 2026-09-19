"""Interpreter/exercise fixtures: seeded sqlite (core.conftest) + mock provider chains injected
into the services (`get_chains` monkeypatched), TTS cache in a temp dir. No network."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from core.conftest import (  # noqa: F401  (re-exported fixtures)
    API,
    actors,
    db_ready,
    seeded,
)
from pydantic import BaseModel

from app.ai.chains import Chains, FallbackChain
from app.ai.providers.base import ProviderError
from app.ai.providers.llm.mock import MockLLM
from app.ai.providers.stt.mock import MockSTT
from app.ai.providers.tts.mock import MockTTS
from app.ai.providers.voice_emotion.mock import MockVoiceEmotion
from app.ai.worker.mock import silence_wav
from app.core.config import get_settings

__all__ = ["API", "actors", "db_ready", "seeded", "silence_wav"]


class FailingLLM:
    name = "mock_fail"
    configured = True

    async def generate(self, **_: Any) -> BaseModel:
        raise ProviderError("forced llm failure")


def make_chains(llm: Any | None = None, stt: Any | None = None, tts: Any | None = None) -> Chains:
    return Chains(
        llm=FallbackChain([llm or MockLLM()], 5, task="llm", circuit_fail_threshold=99),
        stt=FallbackChain([stt or MockSTT()], 5, task="stt", circuit_fail_threshold=99),
        tts=FallbackChain([tts or MockTTS()], 5, task="tts", circuit_fail_threshold=99),
        voice_emotion=FallbackChain([MockVoiceEmotion()], 2, task="voice_emotion"),
    )


@pytest.fixture(autouse=True)
def media_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "media"))
    get_settings.cache_clear()
    return tmp_path / "media"


@pytest.fixture
def chains(monkeypatch: pytest.MonkeyPatch) -> Callable[..., Chains]:
    """`chains(llm=..., stt=...)` swaps the chains both services use; default = plain mocks."""
    from app.modules.exercises import service as exercises_service
    from app.modules.interpreter import service as interpreter_service

    def _install(**kwargs: Any) -> Chains:
        built = make_chains(**kwargs)
        monkeypatch.setattr(interpreter_service, "get_chains", lambda *_a, **_k: built)
        monkeypatch.setattr(exercises_service, "get_chains", lambda *_a, **_k: built)
        return built

    _install()
    return _install
