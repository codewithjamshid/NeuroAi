"""text → (tts_url | None, provider) through the TTS FallbackChain + on-disk cache (TZ §4.8)."""

from app.ai.audio import synthesize_cached
from app.ai.chains import get_chains
from app.core.config import Settings
from app.core.errors import AppError
from app.modules.tts.schemas import TTSOut


class EmptyInputError(AppError):
    status_code = 400
    code = "empty_input"


async def synthesize(settings: Settings, text: str, speed: float | None = None) -> TTSOut:
    """Cache hit → no provider call; all providers down → (None, "browser"), never an error."""
    text = text.strip()
    if not text:
        raise EmptyInputError("text bo'sh")
    tts_url, provider = await synthesize_cached(get_chains(settings), text, speed)
    return TTSOut(tts_url=tts_url, provider=provider)
