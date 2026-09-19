"""Session create/end/transcript, face-metrics batch, state, service helpers."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from core.conftest import API

pytestmark = pytest.mark.usefixtures("seeded")

FACE_BATCH = [
    {
        "ts": 1737000000.0,
        "face_present": True,
        "yaw": 4.1,
        "pitch": -2.0,
        "fsi": 0.71,
        "rest_asym": 0.12,
        "smile_asym": 0.31,
        "brow_asym": 0.18,
        "eye_asym": 0.09,
        "attention": 0.93,
        "fatigue_proxy": 0.22,
        "expr_hint": {"label": "neutral", "conf": 0.4},
        "blendshapes_avg": {"mouthSmileLeft": 0.52, "mouthSmileRight": 0.31},
    },
    {"ts": 1737000001.0, "face_present": False},
]


async def _start(client: AsyncClient, actors: dict[str, Any], mode: str = "companion") -> dict:
    resp = await client.post(
        f"{API}/sessions",
        json={"patient_id": actors["patient_id"], "mode": mode},
        headers=actors["patient"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_end_transcript(client: AsyncClient, actors: dict[str, Any]) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions import service

    session = await _start(client, actors)
    assert set(session) >= {"id", "patient_id", "mode", "started_at"}
    assert session["mode"] == "companion" and session["ended_at"] is None
    sid = uuid.UUID(session["id"])

    async with get_sessionmaker()() as db:
        m1 = await service.create_message(
            db, sid, "patient", "voice", "suv", stt_confidence=0.6, stt_provider="mock"
        )
        m2 = await service.create_message(
            db, sid, "ai", "text", "Suv beraymi?", llm_meta={"model": "mock"}, ignored="x"
        )
    assert m1.stt_confidence == 0.6 and m2.llm_meta == {"model": "mock"}

    ended = await client.post(f"{API}/sessions/{sid}/end", headers=actors["caregiver"])
    assert ended.status_code == 200
    summary = ended.json()["summary"]
    assert set(summary) == {"caregiver_text", "clinician_text", "attention_needed"}
    assert "1 ta javob" in summary["caregiver_text"] and summary["attention_needed"] is False

    transcript = await client.get(f"{API}/sessions/{sid}/transcript", headers=actors["clinician"])
    assert transcript.status_code == 200
    body = transcript.json()
    assert body["session"]["id"] == str(sid) and body["session"]["ended_at"]
    assert body["session"]["summary"]["clinician_text"].startswith("mode=companion")
    assert [m["text"] for m in body["messages"]] == ["suv", "Suv beraymi?"]
    assert set(body["messages"][0]) >= {
        "id",
        "role",
        "modality",
        "text",
        "audio_url",
        "stt_confidence",
        "created_at",
        "llm_meta",
    }
    assert body["messages"][0]["stt_provider"] == "mock"


async def test_invalid_mode_and_foreign_session(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    bad = await client.post(
        f"{API}/sessions",
        json={"patient_id": actors["patient_id"], "mode": "party"},
        headers=actors["patient"],
    )
    assert bad.status_code == 422
    missing = await client.get(
        f"{API}/sessions/{uuid.uuid4()}/transcript", headers=actors["patient"]
    )
    assert missing.status_code == 404


async def test_face_metrics_batch_stored(client: AsyncClient, actors: dict[str, Any]) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import FaceMetric

    session = await _start(client, actors, "exercise")
    resp = await client.post(
        f"{API}/sessions/{session['id']}/face-metrics", json=FACE_BATCH, headers=actors["patient"]
    )
    assert resp.status_code == 200 and resp.json() == {"stored": 2}
    async with get_sessionmaker()() as db:
        rows = (await db.scalars(select(FaceMetric).order_by(FaceMetric.ts))).all()
    assert len(rows) == 2
    assert rows[0].fsi == 0.71 and rows[0].expr_hint == {"label": "neutral", "conf": 0.4}
    assert rows[0].blendshapes_avg["mouthSmileLeft"] == 0.52
    assert rows[1].face_present is False and rows[1].fsi is None


async def test_state_get_default_and_post(client: AsyncClient, actors: dict[str, Any]) -> None:
    session = await _start(client, actors)
    default = await client.get(f"{API}/sessions/{session['id']}/state", headers=actors["caregiver"])
    assert default.status_code == 200
    assert default.json()["engagement"] == "medium" and default.json()["mood"] == "unknown"
    assert default.json()["ts"] is None

    state = {
        "engagement": "low",
        "fatigue": 0.72,
        "mood": "negative",
        "mood_conf": 0.6,
        "distress": True,
        "stt_confidence": 0.41,
        "explain": ["3 ta xato ketma-ket"],
        "inputs": {"face": {"attention": 0.4}},
    }
    posted = await client.post(
        f"{API}/sessions/{session['id']}/state", json=state, headers=actors["patient"]
    )
    assert posted.status_code == 200
    assert posted.json()["ts"] and {k: posted.json()[k] for k in state} == state
    latest = await client.get(f"{API}/sessions/{session['id']}/state", headers=actors["clinician"])
    assert latest.json()["fatigue"] == 0.72 and latest.json()["explain"] == ["3 ta xato ketma-ket"]
    detail = await client.get(f"{API}/sessions/{session['id']}", headers=actors["clinician"])
    assert detail.status_code == 200


async def test_recent_messages_helper(client: AsyncClient, actors: dict[str, Any]) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions import service
    from app.modules.sessions.models import Message

    session = await _start(client, actors)
    sid = uuid.UUID(session["id"])
    async with get_sessionmaker()() as db:
        for i in range(15):
            await service.create_message(
                db, sid, "patient" if i % 2 else "ai", "text", f"m{i}", commit=False
            )
        await db.commit()
        recent = await service.get_recent_messages(db, sid, n=12)
        total = await db.scalar(select(func.count(Message.id)).where(Message.session_id == sid))
    assert total == 15
    assert [m.text for m in recent] == [f"m{i}" for i in range(3, 15)]
