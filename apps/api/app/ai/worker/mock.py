"""Mock worker (TZ §4.4): STT → "salom", TTS → 1 s silence, emotion → neutral.

Used when AI_WORKER_URL=mock so the laptop works without the GPU worker. No ML deps.
"""

import io
import wave

from app.ai.worker.schemas import (
    STTResult,
    STTSegment,
    TTSResult,
    VoiceEmotionResult,
    WorkerHealth,
)

PROVIDER = "worker_mock"
MOCK_MODELS = {"stt": "mock", "tts": "mock", "voice_emotion": "mock", "medllm": "mock"}


def silence_wav(seconds: float = 1.0, sample_rate: int = 16_000) -> bytes:
    """16 kHz mono 16-bit PCM silence; 44-byte RIFF header + 2 bytes per frame."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * int(sample_rate * seconds))
    return buf.getvalue()


class MockWorkerClient:
    mode = "mock"
    base_url = "mock"

    async def health(self) -> WorkerHealth:
        return WorkerHealth(models=dict(MOCK_MODELS), gpu=None)

    async def stt(
        self, wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
    ) -> STTResult:
        return STTResult(
            text="salom",
            confidence=0.9,
            segments=[STTSegment(start=0.0, end=0.6, text="salom", avg_logprob=-0.1)],
            latency_ms=1,
            provider=PROVIDER,
        )

    async def tts(self, text: str, speed: float = 0.85, style: str = "neutral") -> TTSResult:
        return TTSResult(audio_wav=silence_wav(), latency_ms=1, provider=PROVIDER)

    async def voice_emotion(self, wav_bytes: bytes) -> VoiceEmotionResult:
        return VoiceEmotionResult(
            label="neutral",
            scores={"neutral": 1.0},
            arousal=0.0,
            valence=0.0,
            dominance=0.0,
            latency_ms=1,
            provider=PROVIDER,
        )

    async def aclose(self) -> None:
        return None
