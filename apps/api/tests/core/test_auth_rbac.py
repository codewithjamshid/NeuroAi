"""401/403 matrix for the RBAC dependencies (`CurrentUser`, `require_roles`, patient access)."""

import time
from typing import Any

import jwt
import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from core.conftest import API, bearer, register

pytestmark = pytest.mark.usefixtures("seeded")

PATIENT_CARD = {"full_name": "Ikkinchi Bemor", "birth_year": 1970}


async def test_401_missing_token(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


async def test_401_garbage_token(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/patients", headers=bearer("not-a-jwt"))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


async def test_401_refresh_token_as_access(client: AsyncClient, actors: dict[str, Any]) -> None:
    refresh = actors["logins"]["patient"]["refresh"]
    resp = await client.get(f"{API}/me", headers=bearer(refresh))
    assert resp.status_code == 401


async def test_401_expired_token(client: AsyncClient, actors: dict[str, Any]) -> None:
    claims = {
        "sub": actors["logins"]["clinician"]["user"]["id"],
        "role": "clinician",
        "typ": "access",
        "exp": int(time.time()) - 60,
    }
    token = jwt.encode(claims, get_settings().jwt_secret, algorithm="HS256")
    resp = await client.get(f"{API}/me", headers=bearer(token))
    assert resp.status_code == 401


async def test_401_wrong_secret(client: AsyncClient, actors: dict[str, Any]) -> None:
    claims = {"sub": actors["logins"]["clinician"]["user"]["id"], "role": "clinician"}
    claims |= {"typ": "access", "exp": int(time.time()) + 600}
    token = jwt.encode(claims, "other-secret", algorithm="HS256")
    resp = await client.get(f"{API}/me", headers=bearer(token))
    assert resp.status_code == 401


async def test_403_patient_cannot_create_patient(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    resp = await client.post(f"{API}/patients", json=PATIENT_CARD, headers=actors["patient"])
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


async def test_403_caregiver_cannot_create_protocol(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    resp = await client.post(
        f"{API}/patients/{actors['patient_id']}/protocol",
        json={"template_key": "motor_aphasia_m1"},
        headers=actors["caregiver"],
    )
    assert resp.status_code == 403


async def test_403_caregiver_cannot_patch_red_flag(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    resp = await client.patch(
        f"{API}/red-flags/{actors['patient_id']}",
        json={"status": "acknowledged"},
        headers=actors["caregiver"],
    )
    assert resp.status_code == 403


async def test_403_other_clinician_cannot_see_patient(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    other = await register(client, "other@demo.uz", "clinician")
    resp = await client.get(
        f"{API}/patients/{actors['patient_id']}", headers=bearer(other["access"])
    )
    assert resp.status_code == 403
    listed = await client.get(f"{API}/patients", headers=bearer(other["access"]))
    assert listed.status_code == 200 and listed.json() == []


async def test_403_patient_and_caregiver_cannot_see_foreign_patient(
    client: AsyncClient, actors: dict[str, Any]
) -> None:
    other = await register(client, "other2@demo.uz", "clinician")
    created = await client.post(
        f"{API}/patients", json=PATIENT_CARD, headers=bearer(other["access"])
    )
    assert created.status_code == 201
    foreign_id = created.json()["id"]
    for role in ("patient", "caregiver"):
        resp = await client.get(f"{API}/patients/{foreign_id}", headers=actors[role])
        assert resp.status_code == 403, role
        today = await client.get(f"{API}/patients/{foreign_id}/today", headers=actors[role])
        assert today.status_code == 403, role


async def test_404_unknown_patient(client: AsyncClient, actors: dict[str, Any]) -> None:
    resp = await client.get(
        f"{API}/patients/00000000-0000-0000-0000-000000000000", headers=actors["clinician"]
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_roles_see_their_own_patients(client: AsyncClient, actors: dict[str, Any]) -> None:
    for role in ("clinician", "caregiver", "patient"):
        resp = await client.get(f"{API}/patients", headers=actors[role])
        assert resp.status_code == 200, role
        assert [p["id"] for p in resp.json()] == [actors["patient_id"]], role
