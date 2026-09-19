"""Last-resort TTS: no audio, the browser speaks (`speechSynthesis`) or shows text only.

Always succeeds, so it must be the LAST provider in the TTS chain (the registry enforces this).
"""

from app.ai.providers.tts.base import DEFAULT_SPEED, DEFAULT_STYLE, TTSResult


class BrowserTTS:
    name = "browser"
    configured = True

    async def synthesize(
        self, text: str, speed: float = DEFAULT_SPEED, style: str = DEFAULT_STYLE
    ) -> TTSResult:
        return TTSResult(audio_wav=None, provider=self.name, latency_ms=0, browser=True)
