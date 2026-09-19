"""Registry + mock chains end-to-end (no network); cloud adapters constructible without keys."""

from collections.abc import Iterator
from typing import Literal

import pytest
from pydantic import BaseModel, Field

from app.ai.chains import FallbackChain, build_chains, get_chains, recent_calls, reset_chains
from app.ai.providers.base import ProviderError, ProviderUnavailable
from app.ai.providers.llm.base import LLMProvider
from app.ai.providers.llm.gemini import GeminiLLM
from app.ai.providers.llm.mock import MockLLM, build_default
from app.ai.providers.llm.openai import OpenAILLM
from app.ai.providers.stt.base import CLOUD_STT_CONFIDENCE, STTProvider
from app.ai.providers.stt.gemini import GeminiSTT
from app.ai.providers.stt.mock import MockSTT
from app.ai.providers.stt.openai import OpenAISTT
from app.ai.providers.tts.base import TTSProvider
from app.ai.providers.tts.browser import BrowserTTS
from app.ai.providers.tts.mock import MockTTS
from app.ai.providers.tts.openai import OpenAITTS
from app.ai.providers.voice_emotion.base import VoiceEmotionProvider
from app.core.config import Settings

# Ilova B shapes (copied minimally; the content agent owns the real schemas).


class Candidate(BaseModel):
    key: str
    label: str
    emoji: str | None = None
    p: float = Field(ge=0, le=1)


class Risk(BaseModel):
    level: Literal["none", "low", "medium", "high"] = "none"
    category: Literal["self_harm", "stroke_signs", "fall", "none"] = "none"
    evidence: str = ""


class CompanionReply(BaseModel):
    reply_text: str
    tts_text: str
    intent: str
    needs_confirmation: bool = False
    candidates: list[Candidate] = []
    mood_estimate: Literal["negative", "neutral", "positive", "unknown"] = "unknown"
    suggested_action: Literal["none", "offer_break", "start_exercise"] = "none"
    risk: Risk = Risk()


class InterpreterGuess(BaseModel):
    candidates: list[Candidate]
    board_suggested: bool = False
    spoken_text: str
    family_note: str
    follow_up: Literal["none", "body_map", "yes_no"] = "none"


class NextCue(BaseModel):
    level: int = Field(ge=1, le=3)
    text: str


class CoachVerdict(BaseModel):
    result: Literal["correct", "partial", "incorrect"]
    feedback_text: str
    tts_text: str
    next_action: Literal["next_item", "retry_with_cue", "suggest_break"]
    next_cue: NextCue | None = None
    note_for_clinician: str = ""


class PatientState(BaseModel):
    engagement: Literal["low", "medium", "high"]
    fatigue: float = Field(ge=0, le=1)
    mood: Literal["negative", "neutral", "positive", "unknown"]
    mood_conf: float = Field(ge=0, le=1)
    distress: bool = False
    stt_confidence: float | None = None
    explain: list[str] = []
    inputs: dict = {}


@pytest.fixture(autouse=True)
def _reset() -> Iterator[None]:
    reset_chains()
    yield
    reset_chains()


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, gemini_api_key="", openai_api_key="", **overrides)  # type: ignore[arg-type]


def test_default_settings_without_keys_builds_all_chains() -> None:
    ch = build_chains(_settings())
    assert [p.name for p in ch.llm.providers] == ["gemini", "openai", "mock"]  # mock: DEMO_MODE
    assert [p.name for p in ch.stt.providers] == ["worker_mock", "gemini", "openai"]
    assert [p.name for p in ch.tts.providers] == ["worker_mock", "openai", "browser"]
    assert [p.name for p in ch.voice_emotion.providers] == ["worker_mock"]
    assert all(isinstance(p, LLMProvider) for p in ch.llm.providers)
    assert all(isinstance(p, STTProvider) for p in ch.stt.providers)
    assert all(isinstance(p, TTSProvider) for p in ch.tts.providers)
    assert all(isinstance(p, VoiceEmotionProvider) for p in ch.voice_emotion.providers)
    status = ch.status()
    assert set(status) == {"llm", "stt", "tts", "voice_emotion"}
    assert status["llm"][0]["name"] == "gemini" and status["llm"][0]["configured"] is False
    assert status["llm"][2]["configured"] is True
    assert status["stt"][0]["configured"] is True and status["stt"][0]["status"] == "unknown"


def test_no_mock_llm_outside_demo_mode() -> None:
    ch = build_chains(_settings(demo_mode=False))
    assert [p.name for p in ch.llm.providers] == ["gemini", "openai"]


def test_explicit_mock_llm_not_duplicated() -> None:
    ch = build_chains(_settings(llm_providers=["mock"]))
    assert [p.name for p in ch.llm.providers] == ["mock"]


def test_browser_tts_forced_last_and_unknown_names_skipped() -> None:
    ch = build_chains(_settings(tts_providers=["browser", "mock", "nope"]))
    assert [p.name for p in ch.tts.providers] == ["mock", "browser"]


def test_get_chains_cached_per_settings() -> None:
    settings = _settings()
    assert get_chains(settings) is get_chains(settings)
    assert get_chains(_settings()) is not get_chains(settings)


async def test_llm_mock_end_to_end() -> None:
    ch = get_chains(_settings(llm_providers=["mock"]))
    messages = [{"role": "user", "content": "salom"}]
    reply = await ch.llm.call(
        "generate",
        system="s",
        messages=messages,
        schema=CompanionReply,
        temperature=0.4,
        timeout_s=5,
    )
    assert isinstance(reply, CompanionReply)
    assert reply.reply_text.startswith("Salom") and reply.tts_text == reply.reply_text
    assert reply.risk.level == "none" and reply.suggested_action == "none"
    guess = await ch.llm.call("generate", system="s", messages=messages, schema=InterpreterGuess)
    assert isinstance(guess, InterpreterGuess) and len(guess.candidates) == 3
    assert guess.candidates[0].label == "Suv" and sum(c.p for c in guess.candidates) == 1.0
    verdict = await ch.llm.call("generate", system="s", messages=messages, schema=CoachVerdict)
    assert isinstance(verdict, CoachVerdict)
    assert verdict.result == "correct" and verdict.next_action == "next_item"
    assert [r.provider for r in recent_calls()] == ["mock"] * 3


async def test_unconfigured_cloud_llms_skipped_then_mock() -> None:
    ch = get_chains(_settings())  # gemini, openai (no keys) → mock
    reply = await ch.llm.call(
        "generate", system="s", messages=[{"role": "user", "content": "x"}], schema=CompanionReply
    )
    assert isinstance(reply, CompanionReply)
    record = recent_calls()[0]
    assert record.provider == "mock" and record.fallback_index == 2 and record.ok is True
    assert len(recent_calls()) == 1  # unconfigured providers are skipped, not recorded


async def test_stt_tts_voice_emotion_mock_end_to_end() -> None:
    ch = get_chains(_settings())
    stt = await ch.stt.call("transcribe", b"RIFF", lang="uz", initial_prompt="salom")
    assert stt.text == "salom" and stt.confidence == 0.9 and stt.provider == "worker_mock"
    tts = await ch.tts.call("synthesize", "Salom", speed=0.85)
    assert tts.audio_wav is not None and tts.audio_wav[:4] == b"RIFF"
    assert tts.browser is False and tts.provider == "worker_mock"
    emotion = await ch.voice_emotion.call("analyze", b"RIFF")
    assert emotion.label == "neutral" and emotion.provider == "worker_mock"
    assert [r.task for r in recent_calls()] == ["voice_emotion", "tts", "stt"]


async def test_tts_falls_back_to_browser() -> None:
    chain: FallbackChain[TTSProvider] = FallbackChain(
        [MockTTS(fail=True), BrowserTTS()], timeout_s=1, task="tts"
    )
    result = await chain.call("synthesize", "Salom")
    assert result.browser is True and result.audio_wav is None and result.provider == "browser"


async def test_stt_mock_override_and_failure() -> None:
    chain: FallbackChain[STTProvider] = FallbackChain(
        [MockSTT(fail=True), MockSTT(text="suv", confidence=0.7)], timeout_s=1, task="stt"
    )
    result = await chain.call("transcribe", b"RIFF")
    assert (result.text, result.confidence, result.provider) == ("suv", 0.7, "mock")
    only_failing: FallbackChain[STTProvider] = FallbackChain([MockSTT(fail=True)], 1, task="stt")
    with pytest.raises(ProviderUnavailable):
        await only_failing.call("transcribe", b"")


def test_cloud_constructors_without_keys_do_not_fail() -> None:
    providers = (
        GeminiLLM("", "gemini-2.5-flash", "gemini-2.5-pro"),
        OpenAILLM("", "gpt-5-mini"),
        GeminiSTT("", "gemini-2.5-flash"),
        OpenAISTT("", "gpt-4o-transcribe"),
        OpenAITTS("", "gpt-4o-mini-tts", "alloy"),
    )
    assert all(p.configured is False for p in providers)
    assert GeminiLLM("k", "f", "p").configured is True


async def test_unconfigured_cloud_calls_raise_provider_error() -> None:
    with pytest.raises(ProviderError):
        await GeminiLLM("", "f", "p").generate(system="", messages=[], schema=CompanionReply)
    with pytest.raises(ProviderError):
        await OpenAILLM("", "m").generate(system="", messages=[], schema=CompanionReply)
    with pytest.raises(ProviderError):
        await GeminiSTT("", "m").transcribe(b"")
    with pytest.raises(ProviderError):
        await OpenAISTT("", "m").transcribe(b"")
    with pytest.raises(ProviderError):
        await OpenAITTS("", "m", "v").synthesize("x")


def test_build_default_covers_ilova_b_shapes() -> None:
    state = PatientState.model_validate(build_default(PatientState))
    assert state.engagement == "low" and 0 <= state.fatigue <= 1
    assert NextCue.model_validate(build_default(NextCue)).level == 1
    assert CLOUD_STT_CONFIDENCE == 0.5


async def test_mock_llm_overrides_only_known_fields() -> None:
    llm = MockLLM(overrides={"intent": "need", "needs_confirmation": True, "unknown": 1})
    reply = await llm.generate(system="", messages=[], schema=CompanionReply)
    assert isinstance(reply, CompanionReply)
    assert reply.intent == "need" and reply.needs_confirmation is True
