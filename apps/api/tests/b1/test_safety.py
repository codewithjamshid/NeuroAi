"""Safety: keyword → high risk → safe script + red_flags + Telegram/in-app; dedup; medication."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from b1.conftest import API, set_chat_id, start_session

pytestmark = pytest.mark.usefixtures("seeded")

SELF_HARM = "hech narsaning foydasi yo'q, o'lsam yaxshi edi"


async def _rows(model: Any, **where: Any) -> list[Any]:
    from app.db.session import get_sessionmaker

    async with get_sessionmaker()() as db:
        stmt = select(model)
        for key, value in where.items():
            stmt = stmt.where(getattr(model, key) == value)
        return list((await db.scalars(stmt)).all())


async def test_high_risk_keyword_creates_flag_script_and_notifications(
    client: AsyncClient, actors: dict[str, Any], mock_chains: Any, fake_telegram: Any
) -> None:
    from app.ai.prompts.safe_scripts_uz import self_harm_script
    from app.modules.patients.models import RedFlag
    from app.modules.users.models import Notification

    await set_chat_id("qizi@demo.uz", "777001")
    sid = await start_session(client, actors)
    resp = await client.post(
        f"{API}/sessions/{sid}/messages", data={"text": SELF_HARM}, headers=actors["patient"]
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["risk"]["level"] == "high" and body["risk"]["category"] == "self_harm"
    assert body["ai_message"]["text"] == self_harm_script("Nilufar")
    assert "Nilufarga xabar beryapman" in body["ai_message"]["text"]
    assert body["suggested_action"] == "notify_caregiver"
    assert body["state"]["distress"] is True
    assert body["needs_confirmation"] is False

    flags = await _rows(RedFlag, patient_id=uuid.UUID(actors["patient_id"]))
    assert len(flags) == 1
    flag = flags[0]
    assert (flag.category, flag.severity, flag.detector, flag.status) == (
        "self_harm",
        "high",
        "keywords",
        "open",
    )
    assert flag.session_id == uuid.UUID(sid)
    assert flag.notified and flag.notified["telegram"]

    listed = await client.get(
        f"{API}/patients/{actors['patient_id']}/red-flags", headers=actors["clinician"]
    )
    assert listed.status_code == 200 and listed.json()[0]["severity"] == "high"

    sends = [c for c in fake_telegram.calls if c[0] == "sendMessage"]
    assert len(sends) == 1 and sends[0][1]["chat_id"] == "777001"
    assert "o'ziga zarar" in sends[0][1]["text"] and "Bobur" in sends[0][1]["text"]

    notes = await _rows(Notification, kind="red_flag")
    by_channel = sorted((n.channel, n.status) for n in notes)
    assert by_channel == [("inapp", "sent"), ("telegram", "sent")]  # clinician unlinked → inapp

    inbox = await client.get(f"{API}/notifications", headers=actors["caregiver"])
    assert inbox.status_code == 200 and inbox.json()[0]["channel"] == "telegram"
    assert inbox.json()[0]["payload"]["flag_id"] == str(flag.id)

    # the ai message keeps the safety trace
    transcript = await client.get(f"{API}/sessions/{sid}/transcript", headers=actors["clinician"])
    ai = transcript.json()["messages"][-1]
    assert ai["llm_meta"]["safe_script"] is True and ai["llm_meta"]["flag_id"] == str(flag.id)


async def test_same_category_flag_is_deduplicated_within_30_min(
    client: AsyncClient, actors: dict[str, Any], mock_chains: Any, fake_telegram: Any
) -> None:
    from app.modules.patients.models import RedFlag

    await set_chat_id("qizi@demo.uz", "777001")
    sid = await start_session(client, actors)
    for text in (SELF_HARM, "yashashni xohlamayman"):
        resp = await client.post(
            f"{API}/sessions/{sid}/messages", data={"text": text}, headers=actors["patient"]
        )
        assert resp.status_code == 200 and resp.json()["risk"]["level"] == "high"
    flags = await _rows(RedFlag, category="self_harm")
    assert len(flags) == 1
    assert len([c for c in fake_telegram.calls if c[0] == "sendMessage"]) == 1


async def test_llm_risk_is_used_when_keywords_miss(
    client: AsyncClient, actors: dict[str, Any], chains_factory: Any, fake_telegram: Any
) -> None:
    from app.modules.patients.models import RedFlag

    chains_factory(
        {"risk": {"level": "high", "category": "stroke_signs", "evidence": "boshim aylanib"}}
    )
    sid = await start_session(client, actors)
    resp = await client.post(
        f"{API}/sessions/{sid}/messages",
        data={"text": "boshim aylanib ko'zim xira"},
        headers=actors["patient"],
    )
    body = resp.json()
    assert body["risk"]["category"] == "stroke_signs"
    assert "103" in body["ai_message"]["text"] and "tekshiramiz" in body["ai_message"]["text"]
    flag = (await _rows(RedFlag, category="stroke_signs"))[0]
    assert flag.detector == "llm" and flag.evidence == "boshim aylanib"


async def test_medication_question_notifies_clinician(
    client: AsyncClient, actors: dict[str, Any], mock_chains: Any, fake_telegram: Any
) -> None:
    from app.ai.prompts.safe_scripts_uz import medication_reply
    from app.modules.patients.models import RedFlag

    sid = await start_session(client, actors)
    resp = await client.post(
        f"{API}/sessions/{sid}/messages",
        data={"text": "dorimni bugun ikki marta ichsam bo'ladimi?"},
        headers=actors["patient"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ai_message"]["text"] == medication_reply()
    assert body["suggested_action"] == "notify_clinician"
    assert body["risk"] == {
        "level": "low",
        "category": "medication",
        "evidence": "dorimni bugun ikki marta ichsam bo'ladimi?",
    }
    flags = await _rows(RedFlag, category="medication")
    assert len(flags) == 1 and flags[0].severity == "low"
    assert not [c for c in fake_telegram.calls if c[0] == "sendMessage"]  # low → panel only

    # keyword D ("dori ichmadim") → medium → flag + notification fan-out
    resp = await client.post(
        f"{API}/sessions/{sid}/messages",
        data={"text": "kecha dori ichmadim"},
        headers=actors["patient"],
    )
    assert resp.json()["risk"]["level"] == "medium"
    flags = await _rows(RedFlag, category="medication")
    assert len(flags) == 1 and flags[0].severity == "medium"  # reused + escalated


def test_merge_risk_prefers_higher_level() -> None:
    from app.modules.companion.schemas import Risk
    from app.modules.safety.service import merge_risk

    risk, detector, hits = merge_risk(Risk(level="low", category="adherence"), SELF_HARM)
    assert (risk.level, risk.category, detector) == ("high", "self_harm", "keywords")
    assert hits and hits[0]["code"] == "A"
    risk, detector, _ = merge_risk(
        Risk(level="high", category="abuse", evidence="x"), "mashq qilmadim"
    )
    assert (risk.level, risk.category, detector) == ("high", "abuse", "llm")
    risk, detector, _ = merge_risk(None, "o'lib qoldim kulgidan")
    assert (risk.level, detector) == ("none", "llm")
