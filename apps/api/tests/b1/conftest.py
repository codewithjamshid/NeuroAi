"""B1 fixtures: seeded sqlite app (reused from tests/core), mock AI chains injected into the
chains registry, fake Telegram transport (monkeypatched httpx.AsyncClient)."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from core.conftest import (  # noqa: F401  (fixtures re-exported for this package)
    API,
    actors,
    bearer,
    db_ready,
    login,
    seeded,
)
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.config import get_settings

__all__ = ["API", "bearer", "login"]


@pytest.fixture(autouse=True)
def _b1_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "media"))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()


@pytest.fixture
def chains_factory(app: FastAPI) -> Iterator[Callable[..., Any]]:
    """Build mock chains and register them for the app's Settings object."""
    from app.ai import chains as chains_mod
    from app.ai.chains import Chains, FallbackChain
    from app.ai.providers.llm.mock import MockLLM
    from app.ai.providers.stt.mock import MockSTT
    from app.ai.providers.tts.mock import MockTTS
    from app.ai.providers.voice_emotion.mock import MockVoiceEmotion

    def make(
        llm_overrides: dict[str, Any] | None = None,
        *,
        llm_fail: bool = False,
        stt_text: str = "salom",
        stt_confidence: float = 0.9,
    ) -> Chains:
        llm = [] if llm_fail else [MockLLM(llm_overrides or {})]
        chains = Chains(
            llm=FallbackChain(llm, 5.0, task="llm"),
            stt=FallbackChain([MockSTT(stt_text, stt_confidence)], 5.0, task="stt"),
            tts=FallbackChain([MockTTS()], 5.0, task="tts"),
            voice_emotion=FallbackChain([MockVoiceEmotion()], 2.0, task="voice_emotion"),
        )
        settings = get_settings()
        chains_mod._cache[id(settings)] = (settings, chains)
        return chains

    yield make
    chains_mod.reset_chains()


@pytest.fixture
def mock_chains(chains_factory: Callable[..., Any]) -> Any:
    return chains_factory()


class FakeResponse:
    def __init__(self, body: dict[str, Any], status_code: int = 200) -> None:
        self._body = body
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._body


class FakeTelegramHTTP:
    """Stands in for httpx.AsyncClient inside app.modules.notifications.telegram."""

    calls: list[tuple[str, dict[str, Any]]] = []
    updates: list[dict[str, Any]] = []
    fail_send: bool = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def __aenter__(self) -> "FakeTelegramHTTP":
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False

    async def post(self, url: str, json: dict[str, Any] | None = None) -> FakeResponse:
        method = url.rsplit("/", 1)[-1]
        type(self).calls.append((method, dict(json or {})))
        if method == "getMe":
            return FakeResponse({"ok": True, "result": {"username": "sonov1_bot"}})
        if method == "sendMessage":
            if type(self).fail_send:
                return FakeResponse({"ok": False, "description": "chat not found"}, 400)
            return FakeResponse({"ok": True, "result": {"message_id": len(type(self).calls)}})
        if method == "getUpdates":
            pending, type(self).updates = type(self).updates, []
            return FakeResponse({"ok": True, "result": pending})
        return FakeResponse({"ok": False, "description": f"unknown {method}"}, 404)


@pytest.fixture
def fake_telegram(monkeypatch: pytest.MonkeyPatch) -> type[FakeTelegramHTTP]:
    from app.modules.notifications import service as notif_service
    from app.modules.notifications import telegram as tg

    FakeTelegramHTTP.calls, FakeTelegramHTTP.updates, FakeTelegramHTTP.fail_send = [], [], False
    monkeypatch.setattr(tg.httpx, "AsyncClient", FakeTelegramHTTP)
    monkeypatch.setattr(notif_service, "_bot_username", None)
    monkeypatch.setattr(notif_service, "_offset", None)
    notif_service._codes.clear()
    return FakeTelegramHTTP


async def start_session(
    client: AsyncClient, actors: dict[str, Any], mode: str = "companion"  # noqa: F811
) -> str:
    resp = await client.post(
        f"{API}/sessions",
        json={"patient_id": actors["patient_id"], "mode": mode},
        headers=actors["patient"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def set_chat_id(email: str, chat_id: str | None) -> None:
    from sqlalchemy import select

    from app.db.session import get_sessionmaker
    from app.modules.users.models import User

    async with get_sessionmaker()() as db:
        user = await db.scalar(select(User).where(User.email == email))
        assert user is not None
        user.telegram_chat_id = chat_id
        await db.commit()
