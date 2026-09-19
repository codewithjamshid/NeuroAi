"""Gemini Flash audio-in transcription (fallback 1). Confidence is unknown → 0.5 (TZ §5.2)."""

import time
from typing import Any

from google import genai
from google.genai import types

from app.ai.providers.base import ProviderError
from app.ai.providers.stt.base import CLOUD_STT_CONFIDENCE, STTResult

DEFAULT_TIMEOUT_S = 8.0
_INSTRUCTION = (
    "Bu o'zbek tilidagi nutq. Aynan aytilganidek transkripsiya qil. "
    "Faqat transkripsiya matnini qaytar — izohsiz, tarjimasiz, lotin alifbosida."
)


class GeminiSTT:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_s = timeout_s
        self._client: Any = None

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def transcribe(
        self, wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
    ) -> STTResult:
        if not self.configured:
            raise ProviderError("gemini: GEMINI_API_KEY is not set")
        prompt = _INSTRUCTION if lang == "uz" else f"Transcribe this speech (language: {lang})."
        if initial_prompt:
            prompt += f" Kutilayotgan so'zlar: {initial_prompt}."
        contents = [
            types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
            types.Part.from_text(text=prompt),
        ]
        config = types.GenerateContentConfig(
            temperature=0.0,
            http_options=types.HttpOptions(timeout=int(self._timeout_s * 1000)),
        )
        started = time.perf_counter()
        try:
            resp = await self._get_client().aio.models.generate_content(
                model=self._model, contents=contents, config=config
            )
        except Exception as exc:
            raise ProviderError(f"gemini: {type(exc).__name__}: {exc}") from exc
        text = (resp.text or "").strip().strip('"')
        return STTResult(
            text=text,
            confidence=CLOUD_STT_CONFIDENCE,
            segments=[],
            latency_ms=int((time.perf_counter() - started) * 1000),
            provider=self.name,
        )
