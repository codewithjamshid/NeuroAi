"""LLM provider contract: structured output only (TZ §4.3, Ilova B)."""

from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel

Tier = Literal["fast", "pro"]

DEFAULT_TEMPERATURE = 0.4
DEFAULT_TIMEOUT_S = 20.0


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    configured: bool

    async def generate(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
        temperature: float = DEFAULT_TEMPERATURE,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        tier: Tier = "fast",
    ) -> BaseModel: ...
