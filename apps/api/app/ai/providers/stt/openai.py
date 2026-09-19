"""OpenAI `gpt-4o-transcribe` (fallback 2), `language=uz`. Confidence unknown → 0.5 (TZ §5.2)."""

import time
from typing import Any

from openai import AsyncOpenAI

from app.ai.providers.base import ProviderError
from app.ai.providers.stt.base import CLOUD_STT_CONFIDENCE, STTResult

DEFAULT_TIMEOUT_S = 8.0


class OpenAISTT:
    name = "openai"

    def __init__(self, api_key: str, model: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        self._api_key = api_key
        self._model = model
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

    async def transcribe(
        self, wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
    ) -> STTResult:
        if not self.configured:
            raise ProviderError("openai: OPENAI_API_KEY is not set")
        kwargs: dict[str, Any] = {"prompt": initial_prompt} if initial_prompt else {}
        started = time.perf_counter()
        try:
            resp = await self._get_client().audio.transcriptions.create(
                model=self._model,
                file=("audio.wav", wav_bytes, "audio/wav"),
                language=lang,
                response_format="json",
                **kwargs,
            )
        except Exception as exc:
            raise ProviderError(f"openai: {type(exc).__name__}: {exc}") from exc
        return STTResult(
            text=(getattr(resp, "text", "") or "").strip(),
            confidence=CLOUD_STT_CONFIDENCE,
            segments=[],
            latency_ms=int((time.perf_counter() - started) * 1000),
            provider=self.name,
        )
