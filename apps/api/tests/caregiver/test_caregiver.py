"""GET /caregiver/patients/{id}/today and /tips (mock LLM, cache, static fallback, access)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from core.conftest import API, login, register
from httpx import AsyncClient

from app.ai.chains import FallbackChain
from app.ai.providers.llm.mock import MockLLM
from app.modules.caregiver import service as caregiver_service
from app.modules.patients.models import MoodEntry, RedFlag
from app.modules.sessions.models import ExerciseAttempt, Interpretation, PatientState, Session

pytestmark = pytest.mark.usefixtures("seeded")


async def _today_data(patient_id: uuid.UUID) -> None:
    from app.db.session import get_sessionmaker

    now = datetime.now(UTC)
    async with get_sessionmaker()() as db:
        s = Session(
            id=uuid.uuid4(),
            patient_id=patient_id,
            mode="exercise",
            started_at=now - timedelta(minutes=30),
            summary={"caregiver_text": "Bugun 'choy' so'zini aytdi.", "clinician_text": "ok"},
        )
        db.add(s)
        db.add(
            PatientState(
                session_id=s.id,
                ts=now - timedelta(minutes=25),
                engagement="low",
                fatigue=0.7,
                mood="negative",
                mood_conf=0.6,
                distress=False,
                explain=["x"],
            )
        )
        db.add(
            PatientState(
                session_id=s.id,
                ts=now - timedelta(minutes=5),
                engagement="high",
                fatigue=0.2,
                mood="positive",
                mood_conf=0.8,
                distress=False,
            )
        )
        db.add(
            ExerciseAttempt(
                session_id=s.id,
                category="speech",
                expected_answer="choy",
                score=1.0,
                result="correct",
                created_at=now - timedelta(minutes=20),
            )
        )
        db.add(MoodEntry(patient_id=patient_id, ts=now - timedelta(minutes=10), self_score=4))
        for i, key in enumerate(("water", "tea")):
            db.add(
                Interpretation(
                    session_id=s.id,
                    patient_id=patient_id,
                    raw_transcript="s… su",
                    chosen=key,
                    spoken_text=f"Men {key} ichmoqchiman.",
                    family_note="Iliq suv bering.",
                    confirmed_by="patient",
                    created_at=now - timedelta(minutes=15 - i),
                )
            )
        db.add(  # unconfirmed guess: must not appear on the caregiver home
            Interpretation(
                session_id=s.id, patient_id=patient_id, raw_transcript="…", created_at=now
            )
        )
        db.add(
            RedFlag(
                patient_id=patient_id,
                category="fall",
                severity="medium",
                evidence="x",
                detector="keywords",
                status="open",
            )
        )
        await db.commit()


def _chain(tips: list[str] | None, fail: bool = False) -> Any:
    class _Failing:
        name, configured = "fail", True

        async def generate(self, **kw: Any) -> Any:
            raise RuntimeError("down")

    provider = _Failing() if fail else MockLLM(overrides={"tips": tips or []})
    chain: FallbackChain[Any] = FallbackChain([provider], timeout_s=2, task="llm")

    class _Chains:
        llm = chain

    return lambda _settings: _Chains()


async def test_today(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    before = await client.get(f"{API}/caregiver/patients/{pid}/today", headers=actors["caregiver"])
    assert before.status_code == 200, before.text
    assert before.json()["state"] is None and before.json()["exercises_done"] == 0
    assert before.json()["exercises_planned"] == 4  # speech×2 + face + cognitive (fixture template)
    await _today_data(uuid.UUID(pid))
    resp = await client.get(f"{API}/caregiver/patients/{pid}/today", headers=actors["caregiver"])
    body = resp.json()
    assert (
        body["state"]["mood"] == "positive" and body["state"]["engagement"] == "high"
    )  # latest row
    assert body["mood_self"] == 4
    assert body["exercises_done"] == 1 and body["exercises_planned"] == 4
    assert [i["chosen"] for i in body["last_interpretations"]] == ["tea", "water"]  # newest first
    assert body["last_interpretations"][0]["family_note"] == "Iliq suv bering."
    assert body["flags_open"] == 1 and body["tips_cached"] is None
    # patient self + clinician ok; unrelated clinician forbidden
    assert (
        await client.get(f"{API}/caregiver/patients/{pid}/today", headers=actors["patient"])
    ).status_code == 200
    assert (
        await client.get(f"{API}/caregiver/patients/{pid}/today", headers=actors["clinician"])
    ).status_code == 200
    await register(client, "other@demo.uz", "clinician", "Other")
    other = {
        "Authorization": f"Bearer {(await login(client, 'other@demo.uz', 'secret123'))['access']}"
    }
    assert (
        await client.get(f"{API}/caregiver/patients/{pid}/today", headers=other)
    ).status_code == 403


async def test_tips_llm_then_cached(
    client: AsyncClient, actors: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    pid = actors["patient_id"]
    await _today_data(uuid.UUID(pid))
    monkeypatch.setattr(caregiver_service, "get_chains", _chain(["a", "b", "c", "d"]))
    resp = await client.get(f"{API}/caregiver/patients/{pid}/tips", headers=actors["caregiver"])
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"tips": ["a", "b", "c"]}  # truncated to 3
    monkeypatch.setattr(caregiver_service, "get_chains", _chain(None, fail=True))
    again = await client.get(f"{API}/caregiver/patients/{pid}/tips", headers=actors["caregiver"])
    assert again.json() == {"tips": ["a", "b", "c"]}  # served from the (patient, date, hour) cache
    today = await client.get(f"{API}/caregiver/patients/{pid}/today", headers=actors["caregiver"])
    assert today.json()["tips_cached"] == ["a", "b", "c"]


async def test_tips_fallback_when_llm_down_or_short(
    client: AsyncClient, actors: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    pid = actors["patient_id"]
    monkeypatch.setattr(caregiver_service, "get_chains", _chain(None, fail=True))
    resp = await client.get(f"{API}/caregiver/patients/{pid}/tips", headers=actors["caregiver"])
    assert resp.status_code == 200
    assert resp.json()["tips"] == caregiver_service.FALLBACK_TIPS
    assert not caregiver_service._cache  # fallback is not cached
    monkeypatch.setattr(caregiver_service, "get_chains", _chain(["faqat bitta"]))
    short = await client.get(f"{API}/caregiver/patients/{pid}/tips", headers=actors["caregiver"])
    tips = short.json()["tips"]
    assert (
        len(tips) == 3
        and tips[0] == "faqat bitta"
        and tips[1:] == caregiver_service.FALLBACK_TIPS[:2]
    )
    assert (
        await client.get(
            f"{API}/caregiver/patients/{uuid.uuid4()}/tips", headers=actors["caregiver"]
        )
    ).status_code == 404
