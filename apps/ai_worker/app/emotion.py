"""Voice emotion — emotion2vec+ (label, funasr) + audeering wav2vec2 A/V/D (TZ §4.3, §5.3).

Office machine (docs/AI_WORKER_TZ.md): load() creates both models (EMOTION_MODEL, AVD_MODEL);
analyze() returns label + scores from emotion2vec and arousal/valence/dominance from audeering.
"""

import threading
from typing import Any

from app.config import Settings
from app.errors import ModelNotLoaded, ModelUnavailable
from app.schemas import VoiceEmotionResponse

NAME = "voice_emotion"
_model: Any | None = None  # (emotion2vec, audeering) pair once loaded
_lock = threading.Lock()


def is_loaded() -> bool:
    return _model is not None


def load(settings: Settings) -> None:
    global _model
    try:
        from funasr import AutoModel  # noqa: F401  lazy: office GPU only
    except ImportError as exc:
        raise ModelUnavailable("funasr / transformers are not installed (laptop skeleton)") from exc
    # TODO(office):
    #   e2v = AutoModel(model=settings.emotion_model, hub="hf")
    #   avd = <audeering EmotionModel from settings.avd_model, model-card snippet>
    #   _model = (e2v, avd)
    raise ModelUnavailable(
        f"voice-emotion loader not implemented yet ({settings.emotion_model}, {settings.avd_model})"
    )


def unload() -> None:
    global _model
    _model = None


def warmup() -> None:
    # TODO(office): analyze(1 s silence) once.
    return None


def analyze(wav_bytes: bytes) -> VoiceEmotionResponse:
    if _model is None:
        raise ModelNotLoaded(NAME)
    with _lock:
        # TODO(office): e2v.generate(wav, granularity="utterance") → label/scores;
        #   audeering forward → arousal, valence, dominance (0..1).
        raise NotImplementedError("see docs/AI_WORKER_TZ.md")
