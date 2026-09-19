"""TTS provider contract. `browser=True` means "no audio, let speechSynthesis / text handle it"."""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel

DEFAULT_SPEED = 0.85
DEFAULT_STYLE = "neutral"


class TTSResult(BaseModel):
    audio_wav: bytes | None = None
    provider: str
    latency_ms: int = 0
    browser: bool = False


@runtime_checkable
class TTSProvider(Protocol):
    name: str
    configured: bool

    async def synthesize(
        self, text: str, speed: float = DEFAULT_SPEED, style: str = DEFAULT_STYLE
    ) -> TTSResult: ...
