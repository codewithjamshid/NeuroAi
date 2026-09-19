"""STT provider contract (TZ §4.4). Result shape is shared with the worker client."""

from typing import Protocol, runtime_checkable

from app.ai.worker.schemas import STTResult, STTSegment

__all__ = ["CLOUD_STT_CONFIDENCE", "STTProvider", "STTResult", "STTSegment"]

CLOUD_STT_CONFIDENCE = 0.5  # TZ §5.2: Gemini/OpenAI fallback → conf unknown = 0.5


@runtime_checkable
class STTProvider(Protocol):
    name: str
    configured: bool

    async def transcribe(
        self, wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
    ) -> STTResult: ...
