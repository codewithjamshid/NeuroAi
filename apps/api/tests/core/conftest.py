"""Shared fixtures for backend-core tests (imported by test modules; not auto-collected).

Each test gets a fresh in-memory sqlite schema (`create_all`) and the demo seed from
`scripts/seed.py`; protocol templates come from tests/fixtures (the seeds JSON is content-owned).
"""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

FIXTURES = Path(__file__).parent / "fixtures"
TEMPLATES = FIXTURES / "protocol_templates_demo.json"
API = "/api/v1"


@pytest.fixture
async def db_ready(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    from app.db.base import Base
    from app.db.session import dispose_engine, get_engine
    from app.modules.protocols import service as protocols_service

    monkeypatch.setattr(protocols_service, "TEMPLATES_PATH", TEMPLATES)
    await dispose_engine()  # drop any engine cached by a previous test → fresh :memory: db
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await dispose_engine()


@pytest.fixture
async def seeded(db_ready: None) -> dict[str, int]:
    from app.db.session import get_sessionmaker
    from scripts.seed import seed

    async with get_sessionmaker()() as db:
        return await seed(db, templates_path=TEMPLATES)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, email: str, password: str = "demo1234") -> dict[str, Any]:
    resp = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture
async def actors(client: AsyncClient, seeded: dict[str, int]) -> dict[str, Any]:
    """Headers for the 3 demo roles + Bobur's patient_id."""
    clinician = await login(client, "logoped@demo.uz")
    caregiver = await login(client, "qizi@demo.uz")
    patient = await login(client, "bemor@demo.uz")
    return {
        "clinician": bearer(clinician["access"]),
        "caregiver": bearer(caregiver["access"]),
        "patient": bearer(patient["access"]),
        "patient_id": patient["user"]["patient_id"],
        "logins": {"clinician": clinician, "caregiver": caregiver, "patient": patient},
    }


async def register(client: AsyncClient, email: str, role: str, name: str = "X") -> dict[str, Any]:
    payload = {"email": email, "password": "secret123", "full_name": name, "role": role}
    resp = await client.post(f"{API}/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
