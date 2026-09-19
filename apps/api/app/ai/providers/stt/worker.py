"""STT via the AI worker (Kotib/uzbek_stt_v1). `worker_mock` when AI_WORKER_URL=mock."""

from app.ai.worker.client import WorkerClientProtocol
from app.ai.worker.schemas import STTResult


class WorkerSTT:
    configured = True

    def __init__(self, client: WorkerClientProtocol) -> None:
        self._client = client
        self.name = "worker" if client.mode == "http" else "worker_mock"

    async def transcribe(
        self, wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
    ) -> STTResult:
        result = await self._client.stt(wav_bytes, lang=lang, initial_prompt=initial_prompt)
        return result.model_copy(update={"provider": self.name})
