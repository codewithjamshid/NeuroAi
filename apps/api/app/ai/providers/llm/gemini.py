"""Gemini structured output: `response_mime_type=application/json` + `response_schema=<model>`."""

from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.ai.providers.base import ProviderError
from app.ai.providers.llm.base import DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT_S, Tier

_ROLE = {"user": "user", "assistant": "model", "model": "model", "ai": "model"}


class GeminiLLM:
    name = "gemini"

    def __init__(self, api_key: str, model_fast: str, model_pro: str) -> None:
        self._api_key = api_key
        self._models = {"fast": model_fast, "pro": model_pro}
        self._client: Any = None  # lazy: constructing without a key must never fail

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
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
            raise ProviderError("gemini: GEMINI_API_KEY is not set")
        contents = [
            types.Content(
                role=_ROLE.get(m.get("role", "user"), "user"),
                parts=[types.Part.from_text(text=m.get("content", ""))],
            )
            for m in messages
        ] or [types.Content(role="user", parts=[types.Part.from_text(text=" ")])]
        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema,
            http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),
            # 2.5-flash "thinking" adds 3–4 s to dialogue turns; the fast tier answers ≤ 12-word
            # replies and does not need it (TZ §3 latency budget). Pro tier keeps the default.
            thinking_config=(types.ThinkingConfig(thinking_budget=0) if tier == "fast" else None),
        )
        try:
            resp = await self._get_client().aio.models.generate_content(
                model=self._models[tier], contents=contents, config=config
            )
        except Exception as exc:
            raise ProviderError(f"gemini: {type(exc).__name__}: {exc}") from exc
        parsed = getattr(resp, "parsed", None)
        if isinstance(parsed, schema):
            return parsed
        try:
            return schema.model_validate_json(resp.text or "")
        except Exception as exc:
            raise ProviderError(f"gemini: invalid JSON output ({type(exc).__name__})") from exc
