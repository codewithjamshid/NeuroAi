"""TTS — Navoiy (aisha-org/navoiy-tts, CosyVoice2-0.5B), neutral style, speed 0.85 (TZ §4.3).

Office machine (docs/AI_WORKER_TZ.md): fill in load() (CosyVoice2 model from TTS_MODEL_PATH)
and synthesize() (Navoiy text normalization for numbers/abbreviations → 16 kHz mono wav bytes).
"""

import threading
from typing import Any

from app.config import Settings
from app.errors import ModelNotLoaded, ModelUnavailable

NAME = "tts"
_model: Any | None = None
_lock = threading.Lock()


def is_loaded() -> bool:
    return _model is not None


def load(settings: Settings) -> None:
    global _model
    try:
        import torch  # noqa: F401  lazy: office GPU only
    except ImportError as exc:
        raise ModelUnavailable(
            "torch / Navoiy TTS deps are not installed (laptop skeleton)"
        ) from exc
    # TODO(office): _model = <Navoiy/CosyVoice2 inference from settings.tts_model_path>
    raise ModelUnavailable(
        f"Navoiy TTS loader not implemented yet (model path: {settings.tts_model_path})"
    )


def unload() -> None:
    global _model
    _model = None


def warmup() -> None:
    # TODO(office): synthesize("Salom") once.
    return None


def synthesize(text: str, speed: float = 0.85, style: str = "neutral") -> bytes:
    """Return wav bytes (audio/wav, 16 kHz mono)."""
    if _model is None:
        raise ModelNotLoaded(NAME)
    with _lock:
        # TODO(office): normalize text (Navoiy utils), run inference, encode wav with soundfile.
        raise NotImplementedError("see docs/AI_WORKER_TZ.md")
