"""Minimal Telegram Bot API transport (httpx). Tests monkeypatch `httpx.AsyncClient` here."""

import logging
from typing import Any

import httpx

log = logging.getLogger("neuroai.telegram")
logging.getLogger("httpx").setLevel(logging.WARNING)  # httpx INFO logs would print the bot token

API_BASE = "https://api.telegram.org"


class TelegramError(Exception):
    pass


class TelegramClient:
    def __init__(self, token: str, timeout_s: float = 10.0) -> None:
        self._token = token
        self._timeout_s = timeout_s

    @property
    def configured(self) -> bool:
        return bool(self._token)

    def _url(self, method: str) -> str:
        return f"{API_BASE}/bot{self._token}/{method}"

    async def _call(self, method: str, **params: Any) -> Any:
        if not self.configured:
            raise TelegramError("TELEGRAM_BOT_TOKEN is not set")
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            resp = await client.post(self._url(method), json=params)
        try:
            body = resp.json()
        except ValueError as exc:
            raise TelegramError(f"{method}: non-JSON response {resp.status_code}") from exc
        if not body.get("ok"):
            raise TelegramError(f"{method}: {body.get('description') or resp.status_code}")
        return body.get("result")

    async def get_me(self) -> dict[str, Any]:
        return await self._call("getMe")

    async def delete_webhook(self) -> Any:
        """getUpdates is refused (409) while a webhook is set; called once before polling."""
        return await self._call("deleteWebhook", drop_pending_updates=False)

    async def send_message(self, chat_id: str | int, text: str) -> dict[str, Any]:
        return await self._call("sendMessage", chat_id=chat_id, text=text)

    async def get_updates(
        self, offset: int | None = None, long_poll_s: int = 0
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"timeout": long_poll_s, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        return list(await self._call("getUpdates", **params) or [])
