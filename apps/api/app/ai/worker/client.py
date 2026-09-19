"""HTTP client for apps/ai_worker (TZ §4.7).

Every request carries `X-Worker-Key` and `ngrok-skip-browser-warning: 1` (CLAUDE.md).
Timeouts come from settings; callers (FallbackChain, T-04) handle httpx errors.
"""

import time
from typing import Protocol, runtime_checkable

import httpx

from app.ai.worker.mock import MockWorkerClient
from app.ai.worker.schemas import STTResult, TTSResult, VoiceEmotionResult, WorkerHealth
from app.core.config import Settings


@runtime_checkable
class WorkerClientProtocol(Protocol):
    mode: str
    base_url: str

    async def health(self) -> WorkerHealth: ...

    async def stt(
        self, wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
    ) -> STTResult: ...

    async def tts(self, text: str, speed: float = 0.85, style: str = "neutral") -> TTSResult: ...

    async def voice_emotion(self, wav_bytes: bytes) -> VoiceEmotionResult: ...

    async def aclose(self) -> None: ...


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


class WorkerClient:
    mode = "http"

    def __init__(
        self,
        base_url: str,
        key: str,
        timeout_s: float = 4.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-Worker-Key": key, "ngrok-skip-browser-warning": "1"},
            timeout=httpx.Timeout(timeout_s),
            transport=transport,
        )

    @property
    def headers(self) -> httpx.Headers:
        return self._http.headers

    async def health(self) -> WorkerHealth:
        resp = await self._http.get("/health")
        resp.raise_for_status()
        return WorkerHealth.model_validate(resp.json())

    async def stt(
        self, wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
    ) -> STTResult:
        params = {"lang": lang}
        if initial_prompt:
            params["initial_prompt"] = initial_prompt
        started = time.perf_counter()
        resp = await self._http.post(
            "/stt", params=params, files={"audio": ("audio.wav", wav_bytes, "audio/wav")}
        )
        resp.raise_for_status()
        data = resp.json()
        data.setdefault("latency_ms", _elapsed_ms(started))
        return STTResult.model_validate({**data, "provider": "worker"})

    async def tts(self, text: str, speed: float = 0.85, style: str = "neutral") -> TTSResult:
        started = time.perf_counter()
        resp = await self._http.post("/tts", json={"text": text, "speed": speed, "style": style})
        resp.raise_for_status()
        return TTSResult(audio_wav=resp.content, latency_ms=_elapsed_ms(started))

    async def voice_emotion(self, wav_bytes: bytes) -> VoiceEmotionResult:
        started = time.perf_counter()
        resp = await self._http.post(
            "/voice-emotion", files={"audio": ("audio.wav", wav_bytes, "audio/wav")}
        )
        resp.raise_for_status()
        data = resp.json()
        data.setdefault("latency_ms", _elapsed_ms(started))
        return VoiceEmotionResult.model_validate({**data, "provider": "worker"})

    async def aclose(self) -> None:
        await self._http.aclose()


def get_worker_client(settings: Settings) -> WorkerClientProtocol:
    if settings.worker_is_mock:
        return MockWorkerClient()
    return WorkerClient(
        base_url=settings.ai_worker_url,
        key=settings.ai_worker_key,
        timeout_s=settings.ai_worker_timeout_s,
    )
