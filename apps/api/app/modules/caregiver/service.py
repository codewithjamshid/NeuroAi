"""Caregiver home (M8): today's state + LLM tips (cached per patient/date/hour, static fallback)."""

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains import get_chains
from app.ai.prompts.loader import render
from app.ai.providers.base import ProviderUnavailable
from app.core.config import get_settings
from app.modules.caregiver.schemas import CaregiverTodayOut, InterpretationBrief, Tips, TipsOut
from app.modules.patients import service as patients_service
from app.modules.patients.models import Patient
from app.modules.protocols import service as protocols_service
from app.modules.sessions import service as sessions_service
from app.modules.sessions.models import ExerciseAttempt, Interpretation, PatientState, Session
from app.modules.sessions.schemas import PatientStateOut

TIPS_TIMEOUT_S = 20.0
TIPS_TEMPERATURE = 0.5
TIPS_COUNT = 3
FALLBACK_TIPS = [
    "Savollarni 'ha/yo'q' yoki ikki tanlov shaklida bering: 'Choy ichasizmi yoki suv?'",
    "Javobni kamida 10 soniya kuting, gapini bo'lmang va o'rniga tugatmang.",
    "Bugungi mashq so'zini kun davomida 3–4 marta oddiy vaziyatda takrorlang.",
]

_cache: dict[tuple[uuid.UUID, str, int], list[str]] = {}


async def latest_state(db: AsyncSession, patient_id: uuid.UUID) -> PatientStateOut | None:
    stmt = (
        select(PatientState)
        .join(Session, Session.id == PatientState.session_id)
        .where(Session.patient_id == patient_id)
        .order_by(PatientState.ts.desc())
        .limit(1)
    )
    row = await db.scalar(stmt)
    return sessions_service._state_out(row) if row else None


async def latest_summary(db: AsyncSession, patient_id: uuid.UUID) -> str:
    stmt = (
        select(Session.summary)
        .where(Session.patient_id == patient_id, Session.summary.is_not(None))
        .order_by(Session.started_at.desc())
        .limit(1)
    )
    summary = await db.scalar(stmt)
    return str(summary.get("caregiver_text") or "") if isinstance(summary, dict) else ""


async def today_words(db: AsyncSession, patient_id: uuid.UUID) -> list[str]:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = (
        select(ExerciseAttempt.expected_answer)
        .join(Session, Session.id == ExerciseAttempt.session_id)
        .where(
            Session.patient_id == patient_id,
            ExerciseAttempt.created_at >= start,
            ExerciseAttempt.expected_answer.is_not(None),
        )
        .order_by(ExerciseAttempt.created_at)
    )
    words: list[str] = []
    for w in (await db.scalars(stmt)).all():
        if w and w not in words:
            words.append(w)
    return words[:10]


async def last_interpretations(
    db: AsyncSession, patient_id: uuid.UUID, n: int = 5
) -> list[InterpretationBrief]:
    stmt = (  # confirmed requests only (chosen is set by /interpreter/confirm)
        select(Interpretation)
        .where(Interpretation.patient_id == patient_id, Interpretation.chosen.is_not(None))
        .order_by(Interpretation.created_at.desc())
        .limit(n)
    )
    return [InterpretationBrief.model_validate(i) for i in (await db.scalars(stmt)).all()]


def _cache_key(patient_id: uuid.UUID) -> tuple[uuid.UUID, str, int]:
    now = datetime.now(UTC)
    return (patient_id, now.date().isoformat(), now.hour)


async def today(db: AsyncSession, patient: Patient) -> CaregiverTodayOut:
    plan = await protocols_service.build_today(db, patient)
    exercises = [i for i in plan.items if i.kind == "exercise"]
    return CaregiverTodayOut(
        state=await latest_state(db, patient.id),
        mood_self=plan.mood_self,
        exercises_done=sum(1 for i in exercises if i.done),
        exercises_planned=len(exercises),
        last_interpretations=await last_interpretations(db, patient.id),
        flags_open=await patients_service.count_open_flags(db, patient.id),
        tips_cached=_cache.get(_cache_key(patient.id)),
    )


async def tips(db: AsyncSession, patient: Patient) -> TipsOut:
    key = _cache_key(patient.id)
    cached = _cache.get(key)
    if cached:
        return TipsOut(tips=cached)
    state = await latest_state(db, patient.id)
    system = render(
        "caregiver_tips",
        state_json=json.dumps(
            state.model_dump(mode="json", exclude={"inputs"}) if state else {}, ensure_ascii=False
        ),
        today_summary=await latest_summary(db, patient.id),
        today_words=", ".join(await today_words(db, patient.id)),
    )
    generated: list[str] = []
    try:
        result = await get_chains(get_settings()).llm.call(
            "generate",
            system=system,
            messages=[{"role": "user", "content": "Bugungi 3 ta maslahat."}],
            schema=Tips,
            temperature=TIPS_TEMPERATURE,
            timeout_s=TIPS_TIMEOUT_S,
            tier="fast",
        )
        generated = [t.strip() for t in result.tips if isinstance(t, str) and t.strip()]
    except ProviderUnavailable:
        generated = []
    out = (generated + [t for t in FALLBACK_TIPS if t not in generated])[:TIPS_COUNT]
    if generated:
        if len(_cache) > 500:
            _cache.clear()
        _cache[key] = out
    return TipsOut(tips=out)
