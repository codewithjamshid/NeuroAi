"""Offline LLM: builds a minimal valid instance of any response schema (Ilova B shapes)."""

import asyncio
import types
from enum import Enum
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel

from app.ai.providers.llm.base import DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT_S, Tier

_GREETING = "Salom! Sizni eshityapman. Bugun o'zingizni qanday his qilyapsiz?"

# Field-name → sensible Uzbek text, so mock replies look real on the demo screen.
TEXT_DEFAULTS: dict[str, str] = {
    "reply_text": _GREETING,
    "tts_text": _GREETING,
    "intent": "smalltalk",
    "spoken_text": "Menga suv kerak.",
    "family_note": "Bemor suv so'rayapti. Iltimos, yaqinlashib bir stakan suv bering.",
    "feedback_text": "Yaxshi! Davom etamiz.",
    "caregiver_text": "Bugun suhbat yaxshi o'tdi, kayfiyat tinch.",
    "clinician_text": "Sessiya mock rejimida o'tdi; ko'rsatkichlar yo'q.",
    "content_md": "# Haftalik hisobot\n\nMock rejim: ma'lumot yo'q.",
    "text": "Yaxshi, davom etamiz.",
    "title": "Mock",
    "evidence": "",
    "note_for_clinician": "",
}
CANDIDATE_DEFAULTS: list[dict[str, Any]] = [
    {"key": "water", "label": "Suv", "emoji": "💧", "p": 0.6},
    {"key": "pain", "label": "Og'riq", "emoji": "🤕", "p": 0.25},
    {"key": "toilet", "label": "Hojatxona", "emoji": "🚻", "p": 0.15},
]


def build_default(
    schema: type[BaseModel], overrides: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Dict that validates against `schema`: required fields filled, defaults left to pydantic."""
    data: dict[str, Any] = {}
    for name, info in schema.model_fields.items():
        if overrides and name in overrides:
            data[name] = overrides[name]
        elif info.is_required():
            data[name] = _default_for(info.annotation, name)
    return data


def _default_for(annotation: Any, name: str) -> Any:  # noqa: PLR0911
    origin = get_origin(annotation)
    if origin is Annotated:
        return _default_for(get_args(annotation)[0], name)
    if origin is Literal:
        return get_args(annotation)[0]
    if origin in (Union, types.UnionType):
        args = [a for a in get_args(annotation) if a is not type(None)]
        return _default_for(args[0], name) if args else None
    if origin in (list, set, tuple) or annotation is list:
        item = get_args(annotation)[0] if get_args(annotation) else str
        if name == "candidates" and isinstance(item, type) and issubclass(item, BaseModel):
            return [
                build_default(item, {k: v for k, v in c.items() if k in item.model_fields})
                for c in CANDIDATE_DEFAULTS
            ]
        return []
    if origin is dict or annotation is dict:
        return {}
    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            return build_default(annotation)
        if issubclass(annotation, bool):
            return False
        if issubclass(annotation, int):
            return 1
        if issubclass(annotation, float):
            return 0.5
        if issubclass(annotation, str):
            return TEXT_DEFAULTS.get(name, f"mock {name}")
        if issubclass(annotation, Enum):
            return next(iter(annotation)).value
    return None


class MockLLM:
    name = "mock"
    configured = True

    def __init__(self, overrides: dict[str, Any] | None = None, latency_s: float = 0.0) -> None:
        self._overrides = overrides or {}
        self._latency_s = latency_s

    async def generate(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
        temperature: float = DEFAULT_TEMPERATURE,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        tier: Tier = "fast",
    ) -> BaseModel:
        if self._latency_s:
            await asyncio.sleep(self._latency_s)
        overrides = {k: v for k, v in self._overrides.items() if k in schema.model_fields}
        return schema.model_validate(build_default(schema, overrides))
