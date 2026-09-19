"""FallbackChain (TZ §4.4) + registry of the four chains: llm, stt, tts, voice_emotion.

Rules: providers in order; timeout/exception → next; N consecutive failures → circuit open for
`circuit_reset_s` (then one half-open try); every attempt → ProviderCallRecord (ring buffer +
record sink for `provider_calls`); all fail → ProviderUnavailable(task).
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.ai.providers.base import ProviderCallRecord, ProviderUnavailable
from app.ai.providers.llm.base import LLMProvider
from app.ai.providers.llm.gemini import GeminiLLM
from app.ai.providers.llm.mock import MockLLM
from app.ai.providers.llm.openai import OpenAILLM
from app.ai.providers.stt.base import STTProvider
from app.ai.providers.stt.gemini import GeminiSTT
from app.ai.providers.stt.mock import MockSTT
from app.ai.providers.stt.openai import OpenAISTT
from app.ai.providers.stt.worker import WorkerSTT
from app.ai.providers.tts.base import TTSProvider
from app.ai.providers.tts.browser import BrowserTTS
from app.ai.providers.tts.gemini import GeminiTTS
from app.ai.providers.tts.mock import MockTTS
from app.ai.providers.tts.openai import OpenAITTS
from app.ai.providers.tts.worker import WorkerTTS
from app.ai.providers.voice_emotion.base import VoiceEmotionProvider
from app.ai.providers.voice_emotion.mock import MockVoiceEmotion
from app.ai.providers.voice_emotion.worker import WorkerVoiceEmotion
from app.ai.worker.client import WorkerClientProtocol, get_worker_client
from app.core.config import Settings

log = logging.getLogger("neuroai.ai.chains")

RecordSink = Callable[[ProviderCallRecord], Awaitable[None]]

RECENT_CALLS_MAX = 300
LLM_TIMEOUT_S = 25.0
STT_TIMEOUT_S = (
    20.0  # cloud STT (Gemini) needs ≥ 10 s deadline; worker httpx timeout (4 s) fails faster
)
TTS_TIMEOUT_S = 20.0  # Gemini TTS ≈ 5 s per call
VOICE_EMOTION_TIMEOUT_S = 2.0  # TZ §4.8: error → null, never blocks the reply

_recent: deque[ProviderCallRecord] = deque(maxlen=RECENT_CALLS_MAX)
_record_sink: RecordSink | None = None


def set_record_sink(callback: RecordSink | None) -> None:
    """Global async sink for every ProviderCallRecord (next wave: insert into provider_calls)."""
    global _record_sink
    _record_sink = callback


def recent_calls(limit: int = 20) -> list[ProviderCallRecord]:
    """Newest first."""
    items = list(_recent)
    items.reverse()
    return items[:limit]


def _now() -> float:  # monkeypatched in tests to fast-forward the circuit timer
    return time.monotonic()


@dataclass
class _State:
    consecutive_failures: int = 0
    opened_at: float | None = None
    last_ok: bool | None = None
    last_latency_ms: int | None = None
    last_error: str | None = None


class FallbackChain[T]:
    def __init__(
        self,
        providers: list[T],
        timeout_s: float,
        *,
        task: str = "",
        circuit_fail_threshold: int = 3,
        circuit_reset_s: float = 60.0,
        on_record: RecordSink | None = None,
    ) -> None:
        self.providers = list(providers)
        self.timeout_s = timeout_s
        self.task = task
        self.circuit_fail_threshold = circuit_fail_threshold
        self.circuit_reset_s = circuit_reset_s
        self._on_record = on_record
        self._state: dict[str, _State] = {self._name(p): _State() for p in self.providers}

    @staticmethod
    def _name(provider: Any) -> str:
        return getattr(provider, "name", type(provider).__name__)

    @staticmethod
    def _configured(provider: Any) -> bool:
        return bool(getattr(provider, "configured", True))

    def _circuit_open(self, state: _State) -> bool:
        if state.opened_at is None:
            return False
        return _now() - state.opened_at < self.circuit_reset_s  # elapsed → half-open: one try

    async def _emit(self, record: ProviderCallRecord) -> None:
        _recent.append(record)
        for sink in (self._on_record, _record_sink):
            if sink is None:
                continue
            try:
                await sink(record)
            except Exception:
                log.exception("record sink failed", extra={"task": record.task})

    async def call(self, fn_name: str, *args: Any, **kwargs: Any) -> Any:
        task = self.task or fn_name
        for index, provider in enumerate(self.providers):
            name = self._name(provider)
            state = self._state[name]
            if not self._configured(provider) or self._circuit_open(state):
                continue
            started = time.perf_counter()
            try:
                result = await asyncio.wait_for(
                    getattr(provider, fn_name)(*args, **kwargs), timeout=self.timeout_s
                )
            except TimeoutError:
                error = f"ProviderTimeout: {self.timeout_s:g}s"
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"[:300]
            else:
                latency_ms = int((time.perf_counter() - started) * 1000)
                state.consecutive_failures = 0
                state.opened_at = None
                state.last_ok, state.last_latency_ms, state.last_error = True, latency_ms, None
                await self._emit(ProviderCallRecord(name, task, latency_ms, True, index))
                return result
            latency_ms = int((time.perf_counter() - started) * 1000)
            state.consecutive_failures += 1
            state.last_ok, state.last_latency_ms, state.last_error = False, latency_ms, error
            if state.consecutive_failures >= self.circuit_fail_threshold:
                state.opened_at = _now()
            log.warning(
                "provider failed",
                extra={
                    "task": task,
                    "provider": name,
                    "fallback_index": index,
                    "error": error,
                    "circuit": "open" if state.opened_at is not None else "closed",
                },
            )
            await self._emit(ProviderCallRecord(name, task, latency_ms, False, index, error))
        raise ProviderUnavailable(task)

    def status(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for provider in self.providers:
            name = self._name(provider)
            state = self._state[name]
            configured = self._configured(provider)
            if not configured or state.last_ok is None:
                status = "unknown"
            else:
                status = "online" if state.last_ok else "offline"
            out.append(
                {
                    "name": name,
                    "configured": configured,
                    "circuit": "open" if self._circuit_open(state) else "closed",
                    "status": status,
                    "last_ok": state.last_ok,
                    "last_latency_ms": state.last_latency_ms,
                    "last_error": state.last_error,
                }
            )
        return out

    def reset(self) -> None:
        for state in self._state.values():
            state.consecutive_failures, state.opened_at = 0, None


# --- Registry -----------------------------------------------------------------------------


@dataclass
class Chains:
    llm: FallbackChain[LLMProvider]
    stt: FallbackChain[STTProvider]
    tts: FallbackChain[TTSProvider]
    voice_emotion: FallbackChain[VoiceEmotionProvider]

    def status(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "llm": self.llm.status(),
            "stt": self.stt.status(),
            "tts": self.tts.status(),
            "voice_emotion": self.voice_emotion.status(),
        }


def _build(task: str, names: list[str], factories: dict[str, Callable[[], Any]]) -> list[Any]:
    providers: list[Any] = []
    for name in names:
        factory = factories.get(name)
        if factory is None:
            log.warning("unknown provider skipped", extra={"task": task, "provider": name})
            continue
        provider = factory()
        if not provider.configured:
            log.warning("provider not configured", extra={"task": task, "provider": name})
        providers.append(provider)
    return providers


def build_chains(settings: Settings, worker_client: WorkerClientProtocol | None = None) -> Chains:
    client = worker_client or get_worker_client(settings)
    s = settings
    llm = _build(
        "llm",
        s.llm_providers,
        {
            "gemini": lambda: GeminiLLM(s.gemini_api_key, s.gemini_model_fast, s.gemini_model_pro),
            "openai": lambda: OpenAILLM(s.openai_api_key, s.openai_model),
            "mock": MockLLM,
        },
    )
    if not any(p.configured for p in llm) and s.demo_mode:
        log.warning("llm: no configured provider, appending mock (DEMO_MODE)")
        llm.append(MockLLM())
    stt = _build(
        "stt",
        s.stt_providers,
        {
            "worker": lambda: WorkerSTT(client),
            "gemini": lambda: GeminiSTT(s.gemini_api_key, s.gemini_model_fast),
            "openai": lambda: OpenAISTT(s.openai_api_key, s.openai_stt_model),
            "mock": MockSTT,
        },
    )
    tts = _build(
        "tts",
        s.tts_providers,
        {
            "worker": lambda: WorkerTTS(client),
            "gemini": lambda: GeminiTTS(s.gemini_api_key),
            "openai": lambda: OpenAITTS(s.openai_api_key, s.openai_tts_model, s.openai_tts_voice),
            "browser": BrowserTTS,
            "mock": MockTTS,
        },
    )
    tts.sort(key=lambda p: p.name == "browser")  # stable: browser always last
    voice_emotion = _build(
        "voice_emotion",
        s.voice_emotion_providers,
        {"worker": lambda: WorkerVoiceEmotion(client), "mock": MockVoiceEmotion},
    )
    return Chains(
        llm=FallbackChain(llm, LLM_TIMEOUT_S, task="llm"),
        stt=FallbackChain(stt, STT_TIMEOUT_S, task="stt"),
        tts=FallbackChain(tts, TTS_TIMEOUT_S, task="tts"),
        voice_emotion=FallbackChain(voice_emotion, VOICE_EMOTION_TIMEOUT_S, task="voice_emotion"),
    )


_cache: dict[int, tuple[Settings, Chains]] = {}


def get_chains(settings: Settings, worker_client: WorkerClientProtocol | None = None) -> Chains:
    """One Chains per Settings object (get_settings() is cached → app-wide singleton)."""
    entry = _cache.get(id(settings))
    if entry is None or entry[0] is not settings:
        entry = (settings, build_chains(settings, worker_client))
        _cache[id(settings)] = entry
    return entry[1]


def reset_chains() -> None:
    """Tests: drop cached chains and the ring buffer."""
    _cache.clear()
    _recent.clear()
