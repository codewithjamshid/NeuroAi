"""STT — Kotib/uzbek_stt_v1 (Whisper-medium) via faster-whisper / CTranslate2 (TZ §4.3, §4.7).

Office machine (docs/AI_WORKER_TZ.md): run scripts/prepare_models.sh, set MODELS_ENABLED=stt,
STT_MODEL_PATH=./models/kotib-ct2. Heavy imports stay inside load() so the laptop skeleton
boots without them.
"""

import io
import math
import threading
import time
from typing import Any

from app.config import Settings
from app.errors import ModelNotLoaded, ModelUnavailable
from app.schemas import STTResponse, STTSegment

NAME = "stt"
_model: Any | None = None
_lock = threading.Lock()


def is_loaded() -> bool:
    return _model is not None


def load(settings: Settings) -> None:
    global _model
    try:
        from faster_whisper import WhisperModel  # lazy: office GPU only
    except ImportError as exc:
        raise ModelUnavailable("faster-whisper is not installed (laptop skeleton)") from exc
    _model = WhisperModel(
        settings.stt_model_path, device="cuda", compute_type=settings.stt_compute_type
    )


def unload() -> None:
    global _model
    _model = None


def warmup() -> None:
    # TODO(office): transcribe a 1 s silent wav once so the first real request is fast.
    return None


def logprob_to_confidence(avg_logprob: float) -> float:
    """CT2 avg_logprob (<= 0) → [0, 1]."""
    return max(0.0, min(1.0, math.exp(avg_logprob)))


def transcribe(
    wav_bytes: bytes, lang: str = "uz", initial_prompt: str | None = None
) -> STTResponse:
    if _model is None:
        raise ModelNotLoaded(NAME)
    t0 = time.perf_counter()
    with _lock:
        raw_segments, _info = _model.transcribe(
            io.BytesIO(wav_bytes),
            language=lang,
            initial_prompt=initial_prompt or None,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        segments = [
            STTSegment(start=s.start, end=s.end, text=s.text.strip(), avg_logprob=s.avg_logprob)
            for s in raw_segments
        ]
    text = " ".join(s.text for s in segments if s.text).strip()
    confidence = (
        logprob_to_confidence(sum(s.avg_logprob for s in segments) / len(segments))
        if segments
        else 0.0
    )
    return STTResponse(
        text=text,
        confidence=confidence,
        segments=segments,
        latency_ms=int((time.perf_counter() - t0) * 1000),
    )
