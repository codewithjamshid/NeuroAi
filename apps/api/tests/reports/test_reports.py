"""POST /patients/{id}/reports/generate (MockLLM) + GET list + 503 when no LLM."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from core.conftest import API
from httpx import AsyncClient
from sqlalchemy import select

from app.ai.providers.base import ProviderUnavailable
from app.modules.patients.models import RedFlag
from app.modules.reports import service as reports_service
from app.modules.reports.schemas import WeeklyReport
from app.modules.sessions.models import ExerciseAttempt, Report, Session

pytestmark = pytest.mark.usefixtures("seeded")


async def _some_data(patient_id: uuid.UUID) -> None:
    from app.db.session import get_sessionmaker

    now = datetime.now(UTC)
    async with get_sessionmaker()() as db:
        s = Session(
            id=uuid.uuid4(),
            patient_id=patient_id,
            mode="exercise",
            started_at=now - timedelta(days=1),
            summary={"caregiver_text": "yaxshi", "clinician_text": "aniqlik 0.8"},
        )
        db.add(s)
        db.add(
            ExerciseAttempt(
                session_id=s.id,
                category="speech",
                score=0.8,
                result="correct",
                created_at=now - timedelta(days=1),
            )
        )
        db.add(
            RedFlag(
                patient_id=patient_id,
                category="fall",
                severity="medium",
                evidence="yiqildi",
                detector="keywords",
                status="open",
                created_at=now - timedelta(days=2),
            )
        )
        await db.commit()


async def test_generate_and_list(client: AsyncClient, actors: dict[str, Any]) -> None:
    pid = actors["patient_id"]
    await _some_data(uuid.UUID(pid))
    resp = await client.post(
        f"{API}/patients/{pid}/reports/generate?period=7d", headers=actors["clinician"]
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["content_md"].startswith("# Haftalik hisobot")  # MockLLM TEXT_DEFAULTS
    assert body["generated_by"].startswith("mock")
    today = datetime.now(UTC).date()
    assert body["period_end"] == today.isoformat()
    assert body["period_start"] == (today - timedelta(days=6)).isoformat()
    assert len(body["metrics"]["days"]) == 7 and body["metrics"]["flags"] == 1
    assert body["metrics"]["sessions"] == 1 and "adherence_week" in body["metrics"]

    from app.db.session import get_sessionmaker

    async with get_sessionmaker()() as db:
        rows = (await db.scalars(select(Report).where(Report.patient_id == uuid.UUID(pid)))).all()
        assert len(rows) == 1 and rows[0].content_md == body["content_md"]

    second = await client.post(
        f"{API}/patients/{pid}/reports/generate?period=14d", headers=actors["clinician"]
    )
    assert second.status_code == 201
    assert second.json()["period_start"] == (today - timedelta(days=13)).isoformat()
    listed = await client.get(f"{API}/patients/{pid}/reports", headers=actors["clinician"])
    assert listed.status_code == 200
    ids = [r["id"] for r in listed.json()]
    assert ids == [second.json()["id"], body["id"]]  # newest first
    # caregiver may read, not generate
    assert (
        await client.get(f"{API}/patients/{pid}/reports", headers=actors["caregiver"])
    ).status_code == 200
    denied = await client.post(
        f"{API}/patients/{pid}/reports/generate", headers=actors["caregiver"]
    )
    assert denied.status_code == 403
    bad = await client.post(
        f"{API}/patients/{pid}/reports/generate?period=30d", headers=actors["clinician"]
    )
    assert bad.status_code == 422


async def test_generate_503_when_llm_unavailable(
    client: AsyncClient, actors: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Down:
        def __init__(self, *a: Any, **kw: Any) -> None: ...

        async def call(self, *a: Any, **kw: Any) -> Any:
            raise ProviderUnavailable("llm")

    monkeypatch.setattr(reports_service, "FallbackChain", _Down)
    pid = actors["patient_id"]
    resp = await client.post(f"{API}/patients/{pid}/reports/generate", headers=actors["clinician"])
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "llm_unavailable"
    assert (
        await client.get(f"{API}/patients/{pid}/reports", headers=actors["clinician"])
    ).json() == []


def test_prompt_wraps_markdown_in_json_schema() -> None:
    from app.modules.patients.models import Patient

    patient = Patient(full_name="Test Bemor", birth_year=1970, dialect="khorezm")
    text = reports_service.build_system_prompt(patient, "7 kun", [], ["xulosa"], [])
    assert text.endswith(reports_service.OUTPUT_LINE) and "content_md" in text
    assert "Test Bemor" in text and "khorezm" in text and "SKRINING: []" in text
    assert "{patient_profile}" not in text and "{daily_metrics_json}" not in text
    assert WeeklyReport(content_md="# x").content_md == "# x"


async def test_generate_falls_back_to_fast_tier(
    client: AsyncClient, actors: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every provider fails on `pro` (quota/retired model) → same prompt on `fast`, not 503."""
    from app.ai.providers.base import ProviderCallRecord
    from app.core.config import get_settings

    tiers: list[str] = []

    class _ProDown:
        def __init__(self, *a: Any, **kw: Any) -> None:
            self.sink = kw.get("on_record")

        async def call(self, *a: Any, **kw: Any) -> Any:
            tiers.append(kw["tier"])
            if kw["tier"] == "pro":
                await self.sink(ProviderCallRecord("gemini", "llm", 3, False, 0, "429"))
                raise ProviderUnavailable("llm")
            await self.sink(ProviderCallRecord("gemini", "llm", 5, True, 0))
            return WeeklyReport(content_md="# tez hisobot")

    monkeypatch.setattr(reports_service, "FallbackChain", _ProDown)
    pid = actors["patient_id"]
    resp = await client.post(f"{API}/patients/{pid}/reports/generate", headers=actors["clinician"])
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert tiers == ["pro", "fast"]
    assert body["content_md"] == "# tez hisobot"
    assert body["generated_by"] == f"gemini:{get_settings().gemini_model_fast}"
    assert body["metrics"]["llm_tier"] == "fast"
