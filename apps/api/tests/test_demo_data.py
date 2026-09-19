"""scripts/demo_data.py on in-memory sqlite: idempotent, 14 days for Bobur, resolved flag, reset."""

import uuid
from typing import Any

import pytest
from core.conftest import API, TEMPLATES, bearer, db_ready, login, seeded  # noqa: F401
from httpx import AsyncClient
from sqlalchemy import func, select

from app.modules.patients.models import Patient, RedFlag
from app.modules.sessions.models import ExerciseAttempt, Report, Session
from app.modules.users.models import AuditLog, Notification
from scripts.demo_data import DAYS, FLAG_EVIDENCE, load_demo

pytestmark = pytest.mark.usefixtures("seeded")


async def _load(**kw: Any) -> dict[str, Any]:
    from app.db.session import get_sessionmaker

    async with get_sessionmaker()() as db:
        return await load_demo(db, templates_path=TEMPLATES, **kw)


async def _counts(patient_id: uuid.UUID) -> tuple[int, int]:
    from app.db.session import get_sessionmaker

    async with get_sessionmaker()() as db:
        sessions = await db.scalar(
            select(func.count(Session.id)).where(Session.patient_id == patient_id)
        )
        attempts = await db.scalar(
            select(func.count(ExerciseAttempt.id))
            .join(Session, Session.id == ExerciseAttempt.session_id)
            .where(Session.patient_id == patient_id)
        )
        return int(sessions or 0), int(attempts or 0)


async def test_demo_data_idempotent_and_shape(client: AsyncClient) -> None:
    first = await _load()
    assert first["status"] == "loaded"
    assert first["red_flags"] == 1 and first["reports"] == 1 and first["patients_created"] == 1
    assert first["sessions"] >= DAYS and first["exercise_attempts"] >= 6 * DAYS
    bobur = uuid.UUID(first["bobur_id"])
    counts = await _counts(bobur)
    assert counts[0] >= DAYS and counts[1] >= 6 * DAYS
    second = await _load()
    assert second["status"] == "already loaded" and second["bobur_id"] == first["bobur_id"]
    assert await _counts(bobur) == counts  # nothing added by the 2nd run

    from app.db.session import get_sessionmaker

    async with get_sessionmaker()() as db:
        days = await db.scalar(
            select(func.count(func.distinct(func.date(Session.started_at)))).where(
                Session.patient_id == bobur
            )
        )
        assert int(days or 0) >= DAYS
        flag = await db.scalar(select(RedFlag).where(RedFlag.patient_id == bobur))
        assert flag is not None and flag.status == "resolved" and flag.severity == "high"
        assert flag.category == "self_harm" and flag.detector == "llm"
        assert flag.evidence == FLAG_EVIDENCE and flag.note and flag.notified["demo"] is True
        audit = await db.scalar(select(AuditLog).where(AuditLog.entity_id == flag.id))
        assert audit is not None and audit.meta["to"] == "resolved"
        notif = await db.scalar(select(Notification).where(Notification.kind == "red_flag"))
        assert notif is not None and notif.status == "sent" and notif.sent_at is not None
        report = await db.scalar(select(Report).where(Report.patient_id == bobur))
        assert report is not None and report.generated_by == "demo"
        assert "Vrach tekshiruvi uchun takliflar" in report.content_md
        gulnora = await db.get(Patient, uuid.UUID(first["gulnora_id"]))
        assert gulnora is not None and gulnora.dysarthria is True
        assert gulnora.full_name.startswith("Gulnora")

    clinician = bearer((await login(client, "logoped@demo.uz"))["access"])
    caregiver = bearer((await login(client, "qizi@demo.uz"))["access"])
    patient_login = await login(client, "bemor@demo.uz")
    assert patient_login["user"]["patient_id"] == first["bobur_id"]

    # dashboard over the demo data: FSI 0.64 → 0.71, accuracy ↑, week adherence ≈ 86 %
    resp = await client.get(f"{API}/patients/{bobur}/dashboard?days=14", headers=clinician)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["days"]) == DAYS
    assert body["fsi_base"] == pytest.approx(0.64, abs=0.01)
    assert body["days"][-1]["fsi"] == pytest.approx(0.71, abs=0.01)
    assert body["days"][0]["speech_accuracy"] < 0.55 < 0.8 < body["days"][-1]["speech_accuracy"]
    assert body["days"][0]["avg_cue_level"] > 1.8 > 1.0 > body["days"][-1]["avg_cue_level"]
    assert body["days"][-1]["independence"] > body["days"][0]["independence"]
    assert 80 <= body["adherence_week"]["exercise"] <= 92
    assert 80 <= body["adherence_week"]["medication"] <= 92
    assert len(body["flags"]) == 1 and body["flags"][0]["status"] == "resolved"

    patients = (await client.get(f"{API}/clinician/patients", headers=clinician)).json()
    assert {p["full_name"] for p in patients} == {"Bobur Matnazarov", "Gulnora Yusupova"}
    assert all(p["open_flags"] == 0 and p["last_activity"] for p in patients)
    caregiver_view = (await client.get(f"{API}/patients", headers=caregiver)).json()
    assert [p["full_name"] for p in caregiver_view] == ["Bobur Matnazarov"]  # qizi: Bobur only
    today = (await client.get(f"{API}/caregiver/patients/{bobur}/today", headers=caregiver)).json()
    assert today["exercises_done"] >= 1 and len(today["last_interpretations"]) >= 1
    assert today["state"] is not None and today["mood_self"] is not None
    reports = (await client.get(f"{API}/patients/{bobur}/reports", headers=clinician)).json()
    assert len(reports) == 1 and reports[0]["generated_by"] == "demo"


async def test_demo_data_reset_reloads() -> None:
    first = await _load()
    bobur = uuid.UUID(first["bobur_id"])
    before = await _counts(bobur)
    third = await _load(reset=True)
    assert third["status"] == "loaded" and third["reset_sessions"] > 0
    assert third["patients_created"] == 0
    assert await _counts(bobur) == before
