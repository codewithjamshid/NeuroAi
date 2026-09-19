"""Gemini TTS (`gemini-2.5-flash-preview-tts`, voice Kore): inline L16 PCM 24 kHz → wav."""

import io
import re
import time
import wave
from typing import Any

from google import genai
from google.genai import types

from app.ai.providers.base import ProviderError
from app.ai.providers.tts.base import DEFAULT_SPEED, DEFAULT_STYLE, TTSResult

DEFAULT_MODEL = "gemini-2.5-flash-preview-tts"
DEFAULT_VOICE = "Kore"
DEFAULT_TIMEOUT_S = 12.0
_PREFIX = {
    "neutral": "O'zbek tilida, sekin va aniq o'qi: ",
    "calm": "O'zbek tilida, juda sekin, tinchlantiruvchi ohangda o'qi: ",
    "cheerful": "O'zbek tilida, sekin va quvnoq ohangda o'qi: ",
}


def pcm_to_wav(pcm: bytes, rate: int = 24_000, channels: int = 1, sampwidth: int = 2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sampwidth)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def _rate_from_mime(mime: str | None) -> int:
    match = re.search(r"rate=(\d+)", mime or "")
    return int(match.group(1)) if match else 24_000


class GeminiTTS:
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        voice: str = DEFAULT_VOICE,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._voice = voice
        self._timeout_s = timeout_s
        self._client: Any = None

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def synthesize(
        self, text: str, speed: float = DEFAULT_SPEED, style: str = DEFAULT_STYLE
    ) -> TTSResult:
        if not self.configured:
            raise ProviderError("gemini: GEMINI_API_KEY is not set")
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=self._voice)
                )
            ),
            http_options=types.HttpOptions(timeout=int(self._timeout_s * 1000)),
        )
        started = time.perf_counter()
        try:
            resp = await self._get_client().aio.models.generate_content(
                model=self._model,
                contents=_PREFIX.get(style, _PREFIX["neutral"]) + text,
                config=config,
            )
        except Exception as exc:
            raise ProviderError(f"gemini: {type(exc).__name__}: {exc}") from exc
        pcm, mime = b"", None
        for cand in resp.candidates or []:
            for part in (cand.content.parts if cand.content else None) or []:
                blob = getattr(part, "inline_data", None)
                if blob is not None and blob.data:
                    pcm += blob.data
                    mime = mime or blob.mime_type
        if not pcm:
            raise ProviderError("gemini: empty audio")
        if mime and mime.startswith("audio/wav"):
            audio = pcm
        else:
            audio = pcm_to_wav(pcm, rate=_rate_from_mime(mime))
        return TTSResult(
            audio_wav=audio,
            provider=self.name,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
