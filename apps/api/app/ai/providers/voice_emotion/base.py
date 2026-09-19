"""Voice-emotion provider contract (TZ §5.3): label + arousal/valence/dominance from a wav."""

from typing import Protocol, runtime_checkable

from app.ai.worker.schemas import VoiceEmotionResult

__all__ = ["VoiceEmotionProvider", "VoiceEmotionResult"]


@runtime_checkable
class VoiceEmotionProvider(Protocol):
    name: str
    configured: bool

    async def analyze(self, wav_bytes: bytes) -> VoiceEmotionResult: ...
