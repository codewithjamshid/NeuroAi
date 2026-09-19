from typing import Any

import pytest
from httpx import AsyncClient

from core.conftest import API, bearer, login, register

pytestmark = pytest.mark.usefixtures("seeded")


@pytest.mark.parametrize(
    ("email", "role", "name"),
    [
        ("logoped@demo.uz", "clinician", "Dilnoza Karimova"),
        ("qizi@demo.uz", "caregiver", "Nilufar"),
        ("bemor@demo.uz", "patient", "Bobur Matnazarov"),
    ],
)
async def test_login_three_roles(client: AsyncClient, email: str, role: str, name: str) -> None:
    body = await login(client, email)
    assert body["access"] and body["refresh"]
    assert body["user"]["role"] == role
    assert body["user"]["full_name"] == name
    if role == "clinician":
        assert body["user"]["patient_id"] is None
    else:
        assert body["user"]["patient_id"]  # own card / primary linked patient


async def test_login_bad_password(client: AsyncClient) -> None:
    resp = await client.post(
        f"{API}/auth/login", json={"email": "logoped@demo.uz", "password": "nope"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


async def test_login_email_case_insensitive(client: AsyncClient) -> None:
    body = await login(client, "LOGOPED@demo.uz")
    assert body["user"]["role"] == "clinician"


async def test_refresh_rotates_pair(client: AsyncClient) -> None:
    body = await login(client, "qizi@demo.uz")
    resp = await client.post(f"{API}/auth/refresh", json={"refresh": body["refresh"]})
    assert resp.status_code == 200
    pair = resp.json()
    assert set(pair) == {"access", "refresh"}
    me = await client.get(f"{API}/me", headers=bearer(pair["access"]))
    assert me.status_code == 200 and me.json()["role"] == "caregiver"


async def test_refresh_rejects_access_token(client: AsyncClient) -> None:
    body = await login(client, "qizi@demo.uz")
    resp = await client.post(f"{API}/auth/refresh", json={"refresh": body["access"]})
    assert resp.status_code == 401


async def test_me_shapes(client: AsyncClient, actors: dict[str, Any]) -> None:
    for role in ("clinician", "caregiver", "patient"):
        resp = await client.get(f"{API}/me", headers=actors[role])
        assert resp.status_code == 200, resp.text
        me = resp.json()
        assert set(me) == {"id", "role", "full_name", "email", "locale", "patient_id"}
        assert me["role"] == role and me["locale"] == "uz-Latn"
        expected_pid = None if role == "clinician" else actors["patient_id"]
        assert me["patient_id"] == expected_pid


async def test_register_clinician_and_duplicate(client: AsyncClient) -> None:
    body = await register(client, "new@demo.uz", "clinician", "Yangi Vrach")
    assert body["user"]["role"] == "clinician" and body["access"]
    me = await client.get(f"{API}/me", headers=bearer(body["access"]))
    assert me.json()["email"] == "new@demo.uz"
    dup = await client.post(
        f"{API}/auth/register",
        json={
            "email": "new@demo.uz",
            "password": "secret123",
            "full_name": "X",
            "role": "caregiver",
        },
    )
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "email_taken"


async def test_register_rejects_patient_role(client: AsyncClient) -> None:
    resp = await client.post(
        f"{API}/auth/register",
        json={"email": "p@demo.uz", "password": "secret123", "full_name": "X", "role": "patient"},
    )
    assert resp.status_code == 422
