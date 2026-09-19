"""Model registry: MODELS_ENABLED → load()/warmup() at startup, statuses for /health.

Status vocabulary (TZ §4.7 + one extra):
- "loaded"   — load() + warmup() succeeded
- "disabled" — not in MODELS_ENABLED, or its library/model is unavailable on this machine
               (load() raised ModelUnavailable — the laptop skeleton case)
- "error"    — enabled and available, but load()/warmup() failed for a real reason
"""

import logging

from app import emotion, medllm, stt, tts
from app.config import Settings
from app.errors import ModelUnavailable
from app.schemas import ModelStatus

log = logging.getLogger("ai_worker.models")

MODULES = {stt.NAME: stt, tts.NAME: tts, emotion.NAME: emotion, medllm.NAME: medllm}

_failed: dict[str, str] = {}  # model name → reason, only genuine load failures


def load_enabled(settings: Settings) -> dict[str, ModelStatus]:
    _failed.clear()
    for name in settings.enabled_models:
        module = MODULES.get(name)
        if module is None:
            log.warning("MODELS_ENABLED: unknown model %r (known: %s)", name, list(MODULES))
            continue
        try:
            module.load(settings)
            module.warmup()
            log.info("model %s loaded", name)
        except ModelUnavailable as exc:
            log.warning("model %s unavailable here (reported as disabled): %s", name, exc)
        except Exception as exc:
            _failed[name] = str(exc)
            module.unload()
            log.exception("model %s failed to load", name)
    return statuses()


def unload_all() -> None:
    for module in MODULES.values():
        module.unload()
    _failed.clear()


def statuses() -> dict[str, ModelStatus]:
    result: dict[str, ModelStatus] = {}
    for name, module in MODULES.items():
        if module.is_loaded():
            result[name] = "loaded"
        elif name in _failed:
            result[name] = "error"
        else:
            result[name] = "disabled"
    return result
