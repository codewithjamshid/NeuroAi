"""Offline STT: delegates to the worker mock ("salom", conf 0.9); text/failure overridable."""

import asyncio

from app.ai.providers.base import ProviderError
from app.ai.worker.mock import MockWorkerClient
from app.ai.worker.schemas import STTResult


class MockSTT:
    name = "mock"
    configured = True

    def __init__(
        self,
        text: str = "salom",
        confidence: float = 0.9,
        fail: bool = False,
        latency_s: float = 0.0,
    ) -> None:
        self._text = text
        self._confidence = confidence
        self._fail = fail
        self._latency_s = latency_s
        self._worker = MockWorkerClient()

    async def transcribe(
        self, wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
    ) -> STTResult:
        if self._latency_s:
            await asyncio.sleep(self._latency_s)
        if self._fail:
            raise ProviderError("mock stt: forced failure")
        result = await self._worker.stt(wav_bytes, lang=lang, initial_prompt=initial_prompt)
        return result.model_copy(
            update={"provider": self.name, "text": self._text, "confidence": self._confidence}
        )
