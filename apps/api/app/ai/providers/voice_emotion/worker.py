"""Voice emotion via the AI worker (emotion2vec + audeering A/V/D)."""

from app.ai.worker.client import WorkerClientProtocol
from app.ai.worker.schemas import VoiceEmotionResult


class WorkerVoiceEmotion:
    configured = True

    def __init__(self, client: WorkerClientProtocol) -> None:
        self._client = client
        self.name = "worker" if client.mode == "http" else "worker_mock"

    async def analyze(self, wav_bytes: bytes) -> VoiceEmotionResult:
        result = await self._client.voice_emotion(wav_bytes)
        return result.model_copy(update={"provider": self.name})
