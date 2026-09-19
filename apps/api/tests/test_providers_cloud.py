"""Live cloud adapters — skipped unless GEMINI_API_KEY / OPENAI_API_KEY are set (.env or env)."""

import os
from typing import Literal

import pytest
from pydantic import BaseModel

from app.ai.providers.llm.gemini import GeminiLLM
from app.ai.providers.llm.openai import OpenAILLM
from app.ai.providers.stt.gemini import GeminiSTT
from app.ai.providers.stt.openai import OpenAISTT
from app.ai.providers.tts.openai import OpenAITTS
from app.ai.worker.mock import silence_wav
from app.core.config import Settings

_settings = Settings()  # same precedence as the app: env > .env > defaults
LIVE = os.environ.get("LIVE_TESTS") == "1"  # opt-in: real network calls, quota-sensitive
gemini_live = pytest.mark.skipif(
    not (LIVE and _settings.gemini_api_key), reason="LIVE_TESTS=1 + GEMINI_API_KEY required"
)
openai_live = pytest.mark.skipif(
    not (LIVE and _settings.openai_api_key), reason="LIVE_TESTS=1 + OPENAI_API_KEY required"
)

SYSTEM = "Sen o'zbek tilida qisqa, iliq javob beradigan yordamchisan. Faqat JSON qaytar."
MESSAGES = [{"role": "user", "content": "Salom, bugun yaxshiman."}]


class Greeting(BaseModel):
    reply_text: str
    mood: Literal["negative", "neutral", "positive", "unknown"] = "unknown"


@gemini_live
async def test_gemini_llm_structured_output() -> None:
    llm = GeminiLLM(
        _settings.gemini_api_key, _settings.gemini_model_fast, _settings.gemini_model_pro
    )
    reply = await llm.generate(
        system=SYSTEM, messages=MESSAGES, schema=Greeting, temperature=0.2, timeout_s=30
    )
    assert isinstance(reply, Greeting) and reply.reply_text


@openai_live
async def test_openai_llm_structured_output() -> None:
    llm = OpenAILLM(_settings.openai_api_key, _settings.openai_model)
    reply = await llm.generate(
        system=SYSTEM, messages=MESSAGES, schema=Greeting, temperature=0.2, timeout_s=60
    )
    assert isinstance(reply, Greeting) and reply.reply_text


@gemini_live
async def test_gemini_stt_returns_cloud_confidence() -> None:
    stt = GeminiSTT(_settings.gemini_api_key, _settings.gemini_model_fast)
    result = await stt.transcribe(silence_wav(1.0), lang="uz", initial_prompt="salom")
    assert result.confidence == 0.5 and result.provider == "gemini"


@openai_live
async def test_openai_stt_returns_cloud_confidence() -> None:
    stt = OpenAISTT(_settings.openai_api_key, _settings.openai_stt_model)
    result = await stt.transcribe(silence_wav(1.0), lang="uz")
    assert result.confidence == 0.5 and result.provider == "openai"


@openai_live
async def test_openai_tts_returns_wav() -> None:
    tts = OpenAITTS(
        _settings.openai_api_key, _settings.openai_tts_model, _settings.openai_tts_voice
    )
    result = await tts.synthesize("Salom, Bobur aka!", speed=0.85)
    assert result.audio_wav is not None and result.audio_wav[:4] == b"RIFF"
    assert result.browser is False and result.provider == "openai"
