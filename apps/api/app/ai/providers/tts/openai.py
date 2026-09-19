"""OpenAI TTS (`gpt-4o-mini-tts`, voice `alloy`, wav). gpt-4o-* ignore `speed` → instructions."""

import time
from typing import Any

from openai import AsyncOpenAI

from app.ai.providers.base import ProviderError
from app.ai.providers.tts.base import DEFAULT_SPEED, DEFAULT_STYLE, TTSResult

DEFAULT_TIMEOUT_S = 12.0
_STYLE_INSTRUCTIONS = {
    "neutral": "O'zbek tilida, sekin, aniq va iliq ohangda o'qi. Har so'zni ravshan talaffuz qil.",
    "calm": "O'zbek tilida, juda sekin, tinchlantiruvchi va mehribon ohangda o'qi.",
    "cheerful": "O'zbek tilida, sekin va quvnoq, rag'batlantiruvchi ohangda o'qi.",
}


class OpenAITTS:
    name = "openai"

    def __init__(
        self, api_key: str, model: str, voice: str, timeout_s: float = DEFAULT_TIMEOUT_S
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._voice = voice
        self._timeout_s = timeout_s
        self._client: Any = None

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key, timeout=self._timeout_s, max_retries=0
            )
        return self._client

    async def synthesize(
        self, text: str, speed: float = DEFAULT_SPEED, style: str = DEFAULT_STYLE
    ) -> TTSResult:
        if not self.configured:
            raise ProviderError("openai: OPENAI_API_KEY is not set")
        kwargs: dict[str, Any] = {}
        if self._model.startswith("gpt-4o"):
            kwargs["instructions"] = _STYLE_INSTRUCTIONS.get(style, _STYLE_INSTRUCTIONS["neutral"])
        else:
            kwargs["speed"] = speed
        started = time.perf_counter()
        try:
            resp = await self._get_client().audio.speech.create(
                model=self._model,
                voice=self._voice,
                input=text,
                response_format="wav",
                **kwargs,
            )
            audio = resp.content
        except Exception as exc:
            raise ProviderError(f"openai: {type(exc).__name__}: {exc}") from exc
        if not audio:
            raise ProviderError("openai: empty audio")
        return TTSResult(
            audio_wav=audio,
            provider=self.name,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
