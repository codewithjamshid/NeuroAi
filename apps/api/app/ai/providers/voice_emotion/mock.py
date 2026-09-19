"""Offline voice emotion: neutral (delegates to the worker mock)."""

from app.ai.worker.mock import MockWorkerClient
from app.ai.worker.schemas import VoiceEmotionResult


class MockVoiceEmotion:
    name = "mock"
    configured = True

    def __init__(self) -> None:
        self._worker = MockWorkerClient()

    async def analyze(self, wav_bytes: bytes) -> VoiceEmotionResult:
        result = await self._worker.voice_emotion(wav_bytes)
        return result.model_copy(update={"provider": self.name})
