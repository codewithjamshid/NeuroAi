"""TTS via the AI worker (aisha-org/navoiy-tts). `worker_mock` → 1 s silence."""

from app.ai.providers.tts.base import DEFAULT_SPEED, DEFAULT_STYLE, TTSResult
from app.ai.worker.client import WorkerClientProtocol


class WorkerTTS:
    configured = True

    def __init__(self, client: WorkerClientProtocol) -> None:
        self._client = client
        self.name = "worker" if client.mode == "http" else "worker_mock"

    async def synthesize(
        self, text: str, speed: float = DEFAULT_SPEED, style: str = DEFAULT_STYLE
    ) -> TTSResult:
        result = await self._client.tts(text, speed=speed, style=style)
        return TTSResult(
            audio_wav=result.audio_wav, provider=self.name, latency_ms=result.latency_ms
        )
