"""build_summary via mock LLM; Telegram link code + /start binding; provider_calls sink."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from b1.conftest import API, start_session

pytestmark = pytest.mark.usefixtures("seeded")


async def test_end_session_summary_via_llm_and_fallback(
    client: AsyncClient, actors: dict[str, Any], chains_factory: Any, fake_telegram: Any
) -> None:
    chains_factory()
    sid = await start_session(client, actors)
    for text in ("salom", "bugun bog'da ishladim"):
        resp = await client.post(
            f"{API}/sessions/{sid}/messages", data={"text": text}, headers=actors["patient"]
        )
        assert resp.status_code == 200
    ended = await client.post(f"{API}/sessions/{sid}/end", headers=actors["caregiver"])
    assert ended.status_code == 200, ended.text
    summary = ended.json()["summary"]
    assert summary == {
        "caregiver_text": "Bugun suhbat yaxshi o'tdi, kayfiyat tinch.",
        "clinician_text": "Sessiya mock rejimida o'tdi; ko'rsatkichlar yo'q.",
        "attention_needed": False,
    }

    # no LLM → deterministic fallback, attention from flags
    chains_factory(llm_fail=True)
    from app.db.session import get_sessionmaker
    from app.modules.sessions import service
    from app.modules.sessions.models import Session

    async with get_sessionmaker()() as db:
        session = await db.get(Session, uuid.UUID(sid))
        assert session is not None
        data = await service.build_summary(db, session)
    assert data["caregiver_text"] == "Sessiya yakunlandi: 2 ta javob berildi."
    assert data["clinician_text"].startswith("mode=companion, messages=4")
    assert data["attention_needed"] is False


async def test_telegram_link_code_and_start_binding(
    client: AsyncClient, actors: dict[str, Any], fake_telegram: Any
) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.notifications import service
    from app.modules.users.models import User

    status = await client.get(f"{API}/notifications/telegram/status", headers=actors["caregiver"])
    assert status.json() == {"linked": False, "chat_id_masked": None}

    link = await client.post(f"{API}/notifications/telegram/link", headers=actors["caregiver"])
    assert link.status_code == 200, link.text
    code = link.json()["code"]
    assert len(code) == 6 and code.isdigit()
    assert link.json()["bot_username"] == "sonov1_bot"

    fake_telegram.updates = [
        {"update_id": 10, "message": {"chat": {"id": 555123}, "text": "/start 000000"}},
        {"update_id": 11, "message": {"chat": {"id": 555123}, "text": f"/start {code}"}},
    ]
    handled = await service.poll_once(service.get_client())
    assert handled == 2
    assert service._offset == 12
    sends = [c[1] for c in fake_telegram.calls if c[0] == "sendMessage"]
    assert "Kod noto'g'ri" in sends[0]["text"]
    assert sends[1] == {"chat_id": 555123, "text": "NeuroAI ulandi ✅ (Nilufar)"}
    assert service.consume_link_code(code) is None  # single use

    async with get_sessionmaker()() as db:
        user = await db.scalar(select(User).where(User.email == "qizi@demo.uz"))
        assert user is not None and user.telegram_chat_id == "555123"

    status = await client.get(f"{API}/notifications/telegram/status", headers=actors["caregiver"])
    assert status.json() == {"linked": True, "chat_id_masked": "…123"}

    # next poll: nothing new, offset kept
    assert await service.poll_once(service.get_client()) == 0
    getupdates = [c[1] for c in fake_telegram.calls if c[0] == "getUpdates"]
    assert getupdates[-1]["offset"] == 12


async def test_notify_never_raises_and_records_failures(
    actors: dict[str, Any], fake_telegram: Any
) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.notifications.service import notify
    from app.modules.patients.models import Patient
    from app.modules.users.models import Notification, User

    fake_telegram.fail_send = True
    async with get_sessionmaker()() as db:
        caregiver = await db.scalar(select(User).where(User.email == "qizi@demo.uz"))
        assert caregiver is not None
        caregiver.telegram_chat_id = "1"
        await db.commit()
        patient = await db.get(Patient, uuid.UUID(actors["patient_id"]))
        assert patient is not None
        rows = await notify(db, patient, None, "fall", "high", "yiqildim")
        assert sorted((r.channel, r.status) for r in rows) == [
            ("inapp", "sent"),
            ("telegram", "failed"),
        ]
        stored = list((await db.scalars(select(Notification))).all())
        assert len(stored) == 2 and any(r.payload.get("error") for r in stored)


async def test_provider_calls_sink_and_endpoint(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    from app.ai.providers.base import ProviderCallRecord
    from app.modules.observability.sink import provider_call_sink

    await provider_call_sink(ProviderCallRecord("gemini", "llm", 812, True, 0))
    await provider_call_sink(ProviderCallRecord("worker_mock", "stt", 4, False, 0, "boom"))

    resp = await client.get(f"{API}/observability/provider-calls", headers=actors["clinician"])
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) == 2
    assert {r["provider"] for r in rows} == {"gemini", "worker_mock"}
    failed = next(r for r in rows if r["provider"] == "worker_mock")
    assert failed["ok"] is False and failed["error"] == "boom" and failed["latency_ms"] == 4

    limited = await client.get(
        f"{API}/observability/provider-calls?limit=1", headers=actors["clinician"]
    )
    assert len(limited.json()) == 1
    denied = await client.get(f"{API}/observability/provider-calls", headers=actors["patient"])
    assert denied.status_code == 403


async def test_sink_is_registered_as_startup_hook(app: Any, fake_telegram: Any) -> None:
    from app.ai import chains
    from app.core.hooks import run_shutdown, run_startup

    await run_startup(app)
    assert chains._record_sink is not None
    await run_shutdown(app)
    assert chains._record_sink is None
