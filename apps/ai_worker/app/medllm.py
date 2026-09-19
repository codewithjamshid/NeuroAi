"""MedLLM (P2) — google/medgemma-1.5-4b-it, 4-bit (TZ §4.3, §4.7). Clinician-only summaries.

Office machine (docs/AI_WORKER_TZ.md): load() with transformers + bitsandbytes; summarize()
returns Markdown. Never a diagnosis or medication change (TZ §1.4) — prompt lives with the api.
"""

import threading
from typing import Any

from app.config import Settings
from app.errors import ModelNotLoaded, ModelUnavailable
from app.schemas import MedLLMResponse

NAME = "medllm"
_model: Any | None = None
_lock = threading.Lock()


def is_loaded() -> bool:
    return _model is not None


def load(settings: Settings) -> None:
    global _model
    try:
        import transformers  # noqa: F401  lazy: office GPU only
    except ImportError as exc:
        raise ModelUnavailable("transformers is not installed (laptop skeleton)") from exc
    # TODO(office): _model = pipeline("image-text-to-text", model=settings.medllm_model,
    #   quantization 4-bit via BitsAndBytesConfig)
    raise ModelUnavailable(f"MedGemma loader not implemented yet ({settings.medllm_model})")


def unload() -> None:
    global _model
    _model = None


def warmup() -> None:
    return None


def summarize(text: str | None, image_b64: str | None, task: str) -> MedLLMResponse:
    if _model is None:
        raise ModelNotLoaded(NAME)
    with _lock:
        # TODO(office): build prompt for `task`, run generation, return Markdown.
        raise NotImplementedError("see docs/AI_WORKER_TZ.md")
