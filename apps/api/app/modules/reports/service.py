"""Weekly report (M7): Gemini Pro over `clinician.daily_metrics` + session summaries + flags."""

import json
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains import FallbackChain, get_chains, recent_calls
from app.ai.prompts.loader import render
from app.ai.providers.base import ProviderUnavailable
from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.clinician import service as clinician_service
from app.modules.clinician.schemas import DayMetrics
from app.modules.patients.models import Patient, RedFlag
from app.modules.reports.schemas import WeeklyReport
from app.modules.sessions.models import Report, Session

REPORT_TIMEOUT_S = 60.0
REPORT_TEMPERATURE = 0.3
OUTPUT_LINE = 'CHIQISH: faqat JSON {"content_md": "<markdown>"}'
PERIOD_DAYS = {"7d": 7, "14d": 14}


class LLMUnavailableError(AppError):
    status_code = 503
    code = "llm_unavailable"


def _profile(patient: Patient) -> dict:
    year = clinician_service.today_utc().year
    return {
        "full_name": patient.full_name,
        "age": (year - patient.birth_year) if patient.birth_year else None,
        "sex": patient.sex,
        "stroke_date": patient.stroke_date.isoformat() if patient.stroke_date else None,
        "affected_side": patient.affected_side,
        "aphasia_type": patient.aphasia_type,
        "dysarthria": patient.dysarthria,
        "dialect": patient.dialect,
    }


def _metrics_payload(days: list[DayMetrics]) -> list[dict]:
    return [d.model_dump(mode="json", exclude_none=True) for d in days]


def build_system_prompt(
    patient: Patient,
    period: str,
    days: list[DayMetrics],
    summaries: list[str],
    flags: list[dict],
) -> str:
    text = render(
        "weekly_report",
        patient_profile=json.dumps(_profile(patient), ensure_ascii=False),
        period=period,
        daily_metrics_json=json.dumps(_metrics_payload(days), ensure_ascii=False),
        summaries=json.dumps(summaries, ensure_ascii=False),
        red_flags=json.dumps(flags, ensure_ascii=False),
        screenings="[]",
    )
    return f"{text}\n{OUTPUT_LINE}"


def _generated_by(provider: str) -> str:
    s = get_settings()
    model = {"gemini": s.gemini_model_pro, "openai": s.openai_model}.get(provider, provider)
    return f"{provider}:{model}"


async def generate(db: AsyncSession, patient: Patient, period: str) -> Report:
    n_days = PERIOD_DAYS[period]
    end = clinician_service.today_utc()
    start = end - timedelta(days=n_days - 1)
    lo, hi = clinician_service._bounds(start, end)
    days = await clinician_service.daily_metrics(db, patient.id, n_days, end)
    week = await clinician_service.week_adherence(db, patient.id, end)

    sess_stmt = (
        select(Session.summary)
        .where(Session.patient_id == patient.id, Session.started_at >= lo, Session.started_at < hi)
        .order_by(Session.started_at)
    )
    summaries = [
        s.get("clinician_text") or s.get("caregiver_text")
        for s in (await db.scalars(sess_stmt)).all()
        if isinstance(s, dict) and (s.get("clinician_text") or s.get("caregiver_text"))
    ]
    flag_stmt = (
        select(RedFlag)
        .where(RedFlag.patient_id == patient.id, RedFlag.created_at >= lo, RedFlag.created_at < hi)
        .order_by(RedFlag.created_at)
    )
    flags = [
        {
            "date": f.created_at.date().isoformat(),
            "category": f.category,
            "severity": f.severity,
            "status": f.status,
            "evidence": f.evidence,
            "note": f.note,
        }
        for f in (await db.scalars(flag_stmt)).all()
    ]
    system = build_system_prompt(
        patient, f"{start.isoformat()} — {end.isoformat()} ({n_days} kun)", days, summaries, flags
    )

    settings = get_settings()
    chain: FallbackChain = FallbackChain(
        get_chains(settings).llm.providers, REPORT_TIMEOUT_S, task="llm"
    )
    try:
        result = await chain.call(
            "generate",
            system=system,
            messages=[{"role": "user", "content": "Hisobotni tayyorla."}],
            schema=WeeklyReport,
            temperature=REPORT_TEMPERATURE,
            timeout_s=REPORT_TIMEOUT_S,
            tier="pro",
        )
    except ProviderUnavailable as exc:
        raise LLMUnavailableError("Hisobot uchun LLM mavjud emas") from exc
    assert isinstance(result, WeeklyReport)
    calls = recent_calls(1)
    provider = calls[0].provider if calls else "unknown"

    report = Report(
        patient_id=patient.id,
        period_start=start,
        period_end=end,
        content_md=result.content_md,
        metrics={
            "days": _metrics_payload(days),
            "adherence_week": week.model_dump(),
            "flags": len(flags),
            "sessions": len(summaries),
        },
        generated_by=_generated_by(provider),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def list_reports(db: AsyncSession, patient_id: uuid.UUID, limit: int = 20) -> list[Report]:
    stmt = (
        select(Report)
        .where(Report.patient_id == patient_id)
        .order_by(Report.created_at.desc())
        .limit(limit)
    )
    return list((await db.scalars(stmt)).all())
