"""TTS endpoint fixtures: seeded sqlite (core.conftest) + a mock TTS chain injected into the
service (`get_chains` monkeypatched), cache in a temp MEDIA_DIR. No network."""

from collections.abc import Callable
from pathlib import Path

import pytest
from core.conftest import (  # noqa: F401  (re-exported fixtures)
    API,
    actors,
    db_ready,
    seeded,
)

from app.ai.chains import Chains, FallbackChain
from app.ai.providers.llm.mock import MockLLM
from app.ai.providers.stt.mock import MockSTT
from app.ai.providers.tts.mock import MockTTS
from app.ai.providers.voice_emotion.mock import MockVoiceEmotion
from app.core.config import get_settings

__all__ = ["API", "actors", "db_ready", "seeded"]


def make_chains(tts: MockTTS | None = None) -> Chains:
    return Chains(
        llm=FallbackChain([MockLLM()], 5, task="llm", circuit_fail_threshold=99),
        stt=FallbackChain([MockSTT()], 5, task="stt", circuit_fail_threshold=99),
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
    """`chains(tts=MockTTS(fail=True))` swaps the chain the service uses; default = plain mock."""
    from app.modules.tts import service

    def _install(tts: MockTTS | None = None) -> Chains:
        built = make_chains(tts)
        monkeypatch.setattr(service, "get_chains", lambda *_a, **_k: built)
        return built

    _install()
    return _install
