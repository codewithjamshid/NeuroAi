"""Offline TTS: 1 s of 16 kHz silence (reuses the worker mock's `silence_wav`)."""

import asyncio

from app.ai.providers.base import ProviderError
from app.ai.providers.tts.base import DEFAULT_SPEED, DEFAULT_STYLE, TTSResult
from app.ai.worker.mock import silence_wav


class MockTTS:
    name = "mock"
    configured = True

    def __init__(self, seconds: float = 1.0, fail: bool = False, latency_s: float = 0.0) -> None:
        self._seconds = seconds
        self._fail = fail
        self._latency_s = latency_s

    async def synthesize(
        self, text: str, speed: float = DEFAULT_SPEED, style: str = DEFAULT_STYLE
    ) -> TTSResult:
        if self._latency_s:
            await asyncio.sleep(self._latency_s)
        if self._fail:
            raise ProviderError("mock tts: forced failure")
        return TTSResult(audio_wav=silence_wav(self._seconds), provider=self.name, latency_ms=1)
