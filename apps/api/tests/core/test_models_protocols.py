"""Protocol templates, protocol from template, items, medications, /today."""

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from core.conftest import API

pytestmark = pytest.mark.usefixtures("seeded")


async def test_templates_list(client: AsyncClient, actors: dict[str, Any]) -> None:
    resp = await client.get(f"{API}/protocol-templates", headers=actors["clinician"])
    assert resp.status_code == 200
    keys = [t["key"] for t in resp.json()]
    assert keys == ["motor_aphasia_m1", "sensory_aphasia_m1", "dysarthria_m1", "cognitive_focus"]
    item = resp.json()[0]["items"][0]
    assert set(item) >= {"kind", "category", "level", "frequency", "duration_min"}


async def test_templates_missing_file_returns_empty(
    client: AsyncClient, actors: dict[str, Any], monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from app.modules.protocols import service

    monkeypatch.setattr(service, "TEMPLATES_PATH", tmp_path / "nope.json")
    resp = await client.get(f"{API}/protocol-templates", headers=actors["clinician"])
    assert resp.status_code == 200 and resp.json() == []


async def test_seeded_protocol_and_today(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    resp = await client.get(f"{API}/patients/{pid}/protocol", headers=actors["patient"])
    assert resp.status_code == 200
    protocol = resp.json()
    assert protocol["status"] == "active" and protocol["template_key"] == "motor_aphasia_m1"
    assert protocol["title"] == "Motor afaziya, 1-oy"
    assert len(protocol["items"]) == 4

    today = await client.get(f"{API}/patients/{pid}/today", headers=actors["caregiver"])
    assert today.status_code == 200
    body = today.json()
    assert body["date"] == datetime.now(UTC).date().isoformat()
    assert body["mood_self"] is None
    kinds = [i["kind"] for i in body["items"]]
    assert kinds.count("exercise") == 4  # speech ×2, face, cognitive
    assert kinds.count("checkin") == 1
    speech = [i for i in body["items"] if i["category"] == "speech"]
    assert [i["time"] for i in speech] == ["10:00", "17:00"]
    assert all(i["done"] is False for i in body["items"])
    assert speech[0]["title"] == "Nutq mashqi" and speech[0]["duration_min"] == 10
    assert speech[0]["protocol_item_id"]


async def test_today_done_flags(client: AsyncClient, actors: dict[str, Any]) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import ExerciseAttempt

    pid = actors["patient_id"]
    created = await client.post(
        f"{API}/sessions", json={"patient_id": pid, "mode": "exercise"}, headers=actors["patient"]
    )
    assert created.status_code == 201
    sid = uuid.UUID(created.json()["id"])
    async with get_sessionmaker()() as db:
        db.add(ExerciseAttempt(session_id=sid, category="speech", result="correct", score=1.0))
        db.add(ExerciseAttempt(session_id=sid, category="face", result="correct", score=1.0))
        await db.commit()
    await client.post(
        f"{API}/patients/{pid}/mood", json={"self_score": 3}, headers=actors["patient"]
    )

    med = await client.post(
        f"{API}/patients/{pid}/medications",
        json={"name": "Aspirin", "dose": "100 mg", "schedule": {"times": ["09:00", "21:00"]}},
        headers=actors["clinician"],
    )
    assert med.status_code == 201
    med_id = med.json()["id"]
    logged = await client.post(
        f"{API}/medications/{med_id}/log", json={"status": "taken"}, headers=actors["caregiver"]
    )
    assert logged.status_code == 201 and logged.json()["source"] == "caregiver"

    today = (await client.get(f"{API}/patients/{pid}/today", headers=actors["patient"])).json()
    by_key = {(i["kind"], i["category"], i["time"]): i["done"] for i in today["items"]}
    assert by_key[("exercise", "speech", "10:00")] is True
    assert by_key[("exercise", "speech", "17:00")] is False  # only one speech session today
    assert by_key[("exercise", "face", "11:00")] is True
    assert by_key[("exercise", "cognitive", None)] is False
    assert by_key[("checkin", None, "09:00")] is True
    assert by_key[("medication", None, "09:00")] is True
    assert by_key[("medication", None, "21:00")] is False
    assert today["mood_self"] == 3
    med_items = [i for i in today["items"] if i["kind"] == "medication"]
    assert (
        med_items[0]["title"] == "Dori: Aspirin (100 mg)"
        and med_items[0]["medication_id"] == med_id
    )


async def test_create_protocol_custom_items_and_edit(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    pid = actors["patient_id"]
    old = (await client.get(f"{API}/patients/{pid}/protocol", headers=actors["clinician"])).json()
    resp = await client.post(
        f"{API}/patients/{pid}/protocol",
        json={
            "title": "Maxsus",
            "items": [
                {
                    "kind": "exercise",
                    "category": "speech",
                    "level": 2,
                    "frequency": {"times_per_day": 3},
                }
            ],
        },
        headers=actors["clinician"],
    )
    assert resp.status_code == 201, resp.text
    new = resp.json()
    assert new["title"] == "Maxsus" and len(new["items"]) == 1
    assert new["items"][0]["frequency"] == {"times_per_day": 3}

    active = (
        await client.get(f"{API}/patients/{pid}/protocol", headers=actors["clinician"])
    ).json()
    assert active["id"] == new["id"]
    paused = await client.patch(
        f"{API}/protocols/{old['id']}", json={"status": "active"}, headers=actors["clinician"]
    )
    assert paused.status_code == 200 and paused.json()["status"] == "active"
    active_again = (
        await client.get(f"{API}/patients/{pid}/protocol", headers=actors["clinician"])
    ).json()
    assert active_again["id"] == old["id"]

    added = await client.post(
        f"{API}/protocols/{new['id']}/items",
        json={"kind": "exercise", "category": "face", "level": 1, "duration_min": 5},
        headers=actors["clinician"],
    )
    assert added.status_code == 201
    item_id = added.json()["id"]
    edited = await client.patch(
        f"{API}/protocol-items/{item_id}",
        json={"level": 3, "frequency": {"times_per_day": 2, "days": [1, 3, 5]}},
        headers=actors["clinician"],
    )
    assert edited.status_code == 200
    assert edited.json()["level"] == 3 and edited.json()["frequency"]["days"] == [1, 3, 5]
    deleted = await client.delete(f"{API}/protocol-items/{item_id}", headers=actors["clinician"])
    assert deleted.status_code == 204
    gone = await client.patch(
        f"{API}/protocol-items/{item_id}", json={"level": 1}, headers=actors["clinician"]
    )
    assert gone.status_code == 404


async def test_protocol_from_unknown_template(client: AsyncClient, actors: dict[str, Any]) -> None:
    resp = await client.post(
        f"{API}/patients/{actors['patient_id']}/protocol",
        json={"template_key": "nope"},
        headers=actors["clinician"],
    )
    assert resp.status_code == 404 and resp.json()["error"]["code"] == "template_not_found"


async def test_no_active_protocol_returns_null(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    active = (
        await client.get(f"{API}/patients/{pid}/protocol", headers=actors["clinician"])
    ).json()
    done = await client.patch(
        f"{API}/protocols/{active['id']}", json={"status": "done"}, headers=actors["clinician"]
    )
    assert done.status_code == 200
    resp = await client.get(f"{API}/patients/{pid}/protocol", headers=actors["clinician"])
    assert resp.status_code == 200 and resp.json() is None
    today = await client.get(f"{API}/patients/{pid}/today", headers=actors["patient"])
    assert today.status_code == 200 and today.json()["items"] == []


async def test_medications_list(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    empty = await client.get(f"{API}/patients/{pid}/medications", headers=actors["caregiver"])
    assert empty.status_code == 200 and empty.json() == []
    await client.post(
        f"{API}/patients/{pid}/medications", json={"name": "Vit B"}, headers=actors["clinician"]
    )
    listed = await client.get(f"{API}/patients/{pid}/medications", headers=actors["patient"])
    assert [m["name"] for m in listed.json()] == ["Vit B"]
    assert listed.json()[0]["schedule"] == {"times": ["09:00"]}
