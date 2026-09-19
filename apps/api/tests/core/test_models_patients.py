"""Patient CRUD, consent, mood trend, red flags (+ audit log)."""

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.conftest import API, bearer, register

pytestmark = pytest.mark.usefixtures("seeded")


async def test_demo_patient_card(client: AsyncClient, actors: dict[str, Any]) -> None:
    resp = await client.get(f"{API}/patients/{actors['patient_id']}", headers=actors["clinician"])
    assert resp.status_code == 200
    card = resp.json()
    assert card["full_name"] == "Bobur Matnazarov"
    assert card["birth_year"] == 1964 and card["stroke_date"] == "2026-08-05"
    assert card["stroke_type"] == "ischemic" and card["affected_side"] == "left"
    assert card["aphasia_type"] == "motor" and card["dialect"] == "khorezm"
    assert "futbol" in card["interests"]
    assert {m["name"] for m in card["family_members"]} == {"Nilufar", "Sardor", "Hurmat"}
    assert card["clinician_id"] == actors["logins"]["clinician"]["user"]["id"]
    assert card["consent_id"]


async def test_create_patient_with_consent_and_patch(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    payload = {
        "full_name": "Test Bemor",
        "birth_year": 1958,
        "sex": "female",
        "stroke_type": "unknown",
        "dialect": "standard",
        "interests": ["she'r"],
        "consent": {"scopes": {"audio_retention": False}},
    }
    resp = await client.post(f"{API}/patients", json=payload, headers=actors["clinician"])
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["consent_id"] and created["clinician_id"]
    pid = created["id"]

    patched = await client.patch(
        f"{API}/patients/{pid}",
        json={"aphasia_type": "sensory", "habits": ["ertalab sayr"]},
        headers=actors["clinician"],
    )
    assert patched.status_code == 200
    assert patched.json()["aphasia_type"] == "sensory"
    assert patched.json()["habits"] == ["ertalab sayr"]

    listed = await client.get(f"{API}/patients", headers=actors["clinician"])
    assert {p["id"] for p in listed.json()} == {actors["patient_id"], pid}


async def test_caregiver_creates_card_and_cannot_set_aphasia(client: AsyncClient) -> None:
    caregiver = await register(client, "cg@demo.uz", "caregiver", "Parvarishchi")
    headers = bearer(caregiver["access"])
    payload = {"full_name": "Yangi", "aphasia_type": "global", "caregiver_relation": "son"}
    resp = await client.post(f"{API}/patients", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["aphasia_type"] is None  # clinician-only field dropped
    pid = resp.json()["id"]
    me = await client.get(f"{API}/me", headers=headers)
    assert me.json()["patient_id"] == pid  # linked as primary caregiver
    patched = await client.patch(
        f"{API}/patients/{pid}", json={"aphasia_type": "motor"}, headers=headers
    )
    assert patched.status_code == 200 and patched.json()["aphasia_type"] is None


async def test_consent_endpoint(client: AsyncClient, actors: dict[str, Any]) -> None:
    resp = await client.post(
        f"{API}/patients/{actors['patient_id']}/consent",
        json={"scopes": {"audio_retention": True, "data_for_research": True}, "version": "1.1"},
        headers=actors["caregiver"],
    )
    assert resp.status_code == 201
    consent = resp.json()
    assert consent["version"] == "1.1" and consent["scopes"]["data_for_research"] is True
    card = await client.get(f"{API}/patients/{actors['patient_id']}", headers=actors["caregiver"])
    assert card.json()["consent_id"] == consent["id"]


async def test_mood_and_trend(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    for score, role in ((2, "patient"), (4, "caregiver")):
        resp = await client.post(
            f"{API}/patients/{pid}/mood", json={"self_score": score}, headers=actors[role]
        )
        assert resp.status_code == 201
        assert resp.json()["source"] == role
    bad = await client.post(
        f"{API}/patients/{pid}/mood", json={"self_score": 9}, headers=actors["patient"]
    )
    assert bad.status_code == 422

    trend = await client.get(
        f"{API}/patients/{pid}/mood/trend?days=14", headers=actors["clinician"]
    )
    assert trend.status_code == 200
    points = trend.json()
    assert len(points) == 1
    assert points[0]["date"] == datetime.now(UTC).date().isoformat()
    assert points[0]["self_score"] == 3.0 and points[0]["valence"] is None

    today = await client.get(f"{API}/patients/{pid}/today", headers=actors["patient"])
    assert today.json()["mood_self"] == 4


async def test_red_flags_list_patch_and_audit(client: AsyncClient, actors: dict[str, Any]) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.patients.models import RedFlag
    from app.modules.users.models import AuditLog

    pid = uuid.UUID(actors["patient_id"])
    async with get_sessionmaker()() as db:
        flag = RedFlag(
            patient_id=pid,
            category="stroke_signs",
            severity="high",
            evidence="yuzim qiyshaydi",
            detector="keywords",
        )
        db.add(flag)
        await db.commit()
        flag_id = flag.id

    listed = await client.get(
        f"{API}/patients/{pid}/red-flags?status=open", headers=actors["clinician"]
    )
    assert listed.status_code == 200
    assert [f["id"] for f in listed.json()] == [str(flag_id)]
    assert listed.json()[0]["category"] == "stroke_signs"

    patched = await client.patch(
        f"{API}/red-flags/{flag_id}",
        json={"status": "acknowledged", "note": "ko'rdim"},
        headers=actors["clinician"],
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "acknowledged" and patched.json()["note"] == "ko'rdim"

    still_open = await client.get(
        f"{API}/patients/{pid}/red-flags?status=open", headers=actors["caregiver"]
    )
    assert still_open.json() == []

    async with get_sessionmaker()() as db:
        logs = (await db.scalars(select(AuditLog).where(AuditLog.entity_id == flag_id))).all()
    assert len(logs) == 1
    assert logs[0].action == "red_flag.status"
    assert logs[0].actor_id == uuid.UUID(actors["logins"]["clinician"]["user"]["id"])
    assert logs[0].meta == {"from": "open", "to": "acknowledged", "note": "ko'rdim"}
