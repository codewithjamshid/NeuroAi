"""Dashboard aggregates on a 2-day synthetic dataset, clinician patient list, sessions list."""

import uuid
from datetime import UTC, datetime, time, timedelta
from typing import Any

import pytest
from core.conftest import API, login, register
from httpx import AsyncClient

from app.modules.patients.models import MoodEntry, RedFlag
from app.modules.protocols.models import Medication, MedicationLog
from app.modules.sessions.models import (
    ExerciseAttempt,
    FaceMetric,
    Message,
    Session,
    VoiceMetric,
)

pytestmark = pytest.mark.usefixtures("seeded")


def _at(day_offset: int, hour: int) -> datetime:
    day = datetime.now(UTC).date() - timedelta(days=day_offset)
    return datetime.combine(day, time(hour, 0), tzinfo=UTC)


async def _dataset(patient_id: uuid.UUID) -> dict[str, Any]:
    """Yesterday: 4 speech + 1 face attempt, 3 face rows, 2 moods, 2 valences, 2 med logs.
    Today: 2 speech attempts (both independent), 1 med log, 1 open flag."""
    from app.db.session import get_sessionmaker

    y_start, t_start = _at(1, 10), _at(0, 9)
    async with get_sessionmaker()() as db:
        s1 = Session(id=uuid.uuid4(), patient_id=patient_id, mode="exercise", started_at=y_start)
        s2 = Session(id=uuid.uuid4(), patient_id=patient_id, mode="exercise", started_at=t_start)
        db.add_all([s1, s2])
        speech = [
            (1.0, "correct", 0),
            (0.6, "partial", 1),
            (0.2, "incorrect", 2),
            (1.0, "correct", 1),
        ]
        for i, (score, result, cue) in enumerate(speech):
            db.add(
                ExerciseAttempt(
                    session_id=s1.id,
                    category="speech",
                    score=score,
                    result=result,
                    cue_level=cue,
                    created_at=y_start + timedelta(minutes=i),
                )
            )
        db.add(
            ExerciseAttempt(
                session_id=s1.id,
                category="face",
                score=0.8,
                result="correct",
                cue_level=0,
                created_at=y_start + timedelta(minutes=5),
            )
        )
        for i in range(2):
            db.add(
                ExerciseAttempt(
                    session_id=s2.id,
                    category="speech",
                    score=0.9,
                    result="correct",
                    cue_level=0,
                    created_at=t_start + timedelta(minutes=i),
                )
            )
        for fsi, present in ((0.6, True), (0.7, True), (0.9, False)):
            db.add(
                FaceMetric(
                    session_id=s1.id,
                    ts=y_start.timestamp(),
                    fsi=fsi,
                    face_present=present,
                    created_at=y_start,
                )
            )
        for score in (2, 4):
            db.add(MoodEntry(patient_id=patient_id, ts=y_start, self_score=score))
        for valence in (-0.2, 0.4):
            m = Message(
                id=uuid.uuid4(),
                session_id=s1.id,
                role="patient",
                modality="voice",
                text="…",
                created_at=y_start,
            )
            db.add(m)
            db.add(VoiceMetric(message_id=m.id, valence=valence))
        med = Medication(id=uuid.uuid4(), patient_id=patient_id, name="Dori A")
        db.add(med)
        db.add(MedicationLog(medication_id=med.id, scheduled_at=y_start, status="taken"))
        db.add(MedicationLog(medication_id=med.id, scheduled_at=_at(1, 21), status="missed"))
        db.add(MedicationLog(medication_id=med.id, scheduled_at=t_start, status="taken"))
        db.add(
            RedFlag(
                patient_id=patient_id,
                session_id=s2.id,
                category="self_harm",
                severity="high",
                evidence="x",
                detector="llm",
                status="open",
                created_at=t_start,
            )
        )
        await db.commit()
    return {"s1": s1.id, "s2": s2.id, "t_start": t_start}


async def test_dashboard_aggregates(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    data = await _dataset(uuid.UUID(pid))
    resp = await client.get(f"{API}/patients/{pid}/dashboard?days=3", headers=actors["clinician"])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    days = body["days"]
    assert len(days) == 3 and [d["date"] for d in days] == sorted(d["date"] for d in days)
    empty, yday, today = days
    assert empty["speech_accuracy"] is None and empty["fsi"] is None
    assert empty["adherence_exercise"] == 0.0 and empty["adherence_medication"] is None
    assert yday["speech_accuracy"] == pytest.approx(0.7)
    assert yday["independence"] == 0.25  # 1 correct with cue 0 out of 4 speech attempts
    assert yday["avg_cue_level"] == 1.0
    assert yday["fsi"] == pytest.approx(0.65)  # face_present=False row excluded
    assert yday["mood_self"] == 3.0
    assert yday["valence"] == pytest.approx(0.1)
    assert yday["adherence_exercise"] == pytest.approx(66.7)  # speech+face of 3 planned
    assert yday["adherence_medication"] == 50.0
    assert today["speech_accuracy"] == 0.9 and today["independence"] == 1.0
    assert today["avg_cue_level"] == 0.0 and today["adherence_exercise"] == pytest.approx(33.3)
    assert today["adherence_medication"] == 100.0
    assert body["fsi_base"] == pytest.approx(0.65)
    assert body["sessions_count"] == 2
    assert body["adherence_week"] == {
        "exercise": pytest.approx(14.3),
        "medication": pytest.approx(66.7),
    }
    assert len(body["flags"]) == 1 and body["flags"][0]["status"] == "open"
    assert body["flags"][0]["session_id"] == str(data["s2"])


async def test_clinician_patient_list(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    empty = await client.get(f"{API}/clinician/patients", headers=actors["clinician"])
    assert empty.status_code == 200
    assert empty.json()[0]["last_activity"] is None and empty.json()[0]["open_flags"] == 0
    data = await _dataset(uuid.UUID(pid))
    resp = await client.get(f"{API}/clinician/patients", headers=actors["clinician"])
    rows = resp.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == pid and row["full_name"] == "Bobur Matnazarov"
    assert row["age"] == datetime.now(UTC).year - 1964 and row["aphasia_type"] == "motor"
    assert row["open_flags"] == 1
    assert datetime.fromisoformat(row["last_activity"]) == data["t_start"]
    assert row["adherence_week"] == pytest.approx(14.3)
    assert (
        await client.get(f"{API}/clinician/patients", headers=actors["caregiver"])
    ).status_code == 403
    assert (
        await client.get(f"{API}/clinician/patients", headers=actors["patient"])
    ).status_code == 403


async def test_sessions_list_and_access(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    data = await _dataset(uuid.UUID(pid))
    resp = await client.get(
        f"{API}/clinician/patients/{pid}/sessions?limit=30", headers=actors["clinician"]
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert [r["id"] for r in rows] == [str(data["s2"]), str(data["s1"])]  # newest first
    assert rows[0]["accuracy"] == 0.9 and rows[0]["attempts"] == 2 and rows[0]["mode"] == "exercise"
    assert rows[1]["accuracy"] == pytest.approx(0.72) and rows[1]["attempts"] == 5
    assert rows[1]["summary"] is None and rows[1]["ended_at"] is None
    limited = await client.get(
        f"{API}/clinician/patients/{pid}/sessions?limit=1", headers=actors["clinician"]
    )
    assert len(limited.json()) == 1
    # another clinician does not own Bobur
    await register(client, "other@demo.uz", "clinician", "Other")
    other = await login(client, "other@demo.uz", "secret123")
    headers = {"Authorization": f"Bearer {other['access']}"}
    assert (
        await client.get(f"{API}/clinician/patients/{pid}/sessions", headers=headers)
    ).status_code == 403
    assert (await client.get(f"{API}/patients/{pid}/dashboard", headers=headers)).status_code == 403
    assert (await client.get(f"{API}/clinician/patients", headers=headers)).json() == []
    # patient may read own dashboard; unknown patient → 404
    assert (
        await client.get(f"{API}/patients/{pid}/dashboard", headers=actors["patient"])
    ).status_code == 200
    missing = await client.get(
        f"{API}/patients/{uuid.uuid4()}/dashboard", headers=actors["clinician"]
    )
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"
