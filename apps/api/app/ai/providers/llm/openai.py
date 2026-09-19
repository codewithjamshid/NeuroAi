"""OpenAI structured output via `chat.completions.parse(response_format=<pydantic>)`."""

from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.ai.providers.base import ProviderError
from app.ai.providers.llm.base import DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT_S, Tier

PRO_MODEL = "gpt-5"
# Reasoning models reject `temperature`; omit it for them.
_NO_TEMPERATURE_PREFIXES = ("gpt-5", "o1", "o3", "o4")


class OpenAILLM:
    name = "openai"

    def __init__(self, api_key: str, model: str, pro_model: str = PRO_MODEL) -> None:
        self._api_key = api_key
        self._models = {"fast": model, "pro": pro_model}
        self._client: Any = None

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self._api_key, max_retries=0)
        return self._client

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
        if not self.configured:
            raise ProviderError("openai: OPENAI_API_KEY is not set")
        model = self._models[tier]
        kwargs: dict[str, Any] = {}
        if not model.startswith(_NO_TEMPERATURE_PREFIXES):
            kwargs["temperature"] = temperature
        chat: list[Any] = [{"role": "system", "content": system}, *messages]
        try:
            completion = await self._get_client().chat.completions.parse(
                model=model,
                messages=chat,
                response_format=schema,
                timeout=timeout_s,
                **kwargs,
            )
        except Exception as exc:
            raise ProviderError(f"openai: {type(exc).__name__}: {exc}") from exc
        message = completion.choices[0].message
        if message.parsed is None:
            raise ProviderError(f"openai: no parsed output ({message.refusal or 'empty'})")
        return message.parsed
