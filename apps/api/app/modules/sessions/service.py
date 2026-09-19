"""Sessions, messages, face metrics, patient state. `create_message` / `get_recent_messages` /
`build_summary` are the helpers the companion wave builds on."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients import service as patients_service
from app.modules.patients.models import Patient
from app.modules.sessions.models import FaceMetric, Message, PatientState, Session
from app.modules.sessions.schemas import FaceMetricIn, PatientStateIn, PatientStateOut
from app.modules.users.errors import NotFoundError
from app.modules.users.models import User


async def create_session(db: AsyncSession, patient: Patient, user: User, mode: str) -> Session:
    session = Session(
        patient_id=patient.id, mode=mode, device_user_id=user.id, started_at=datetime.now(UTC)
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Session:
    session = await db.get(Session, session_id)
    if session is None:
        raise NotFoundError("Sessiya topilmadi")
    return session


async def get_session_for_user(db: AsyncSession, session_id: uuid.UUID, user: User) -> Session:
    session = await get_session(db, session_id)
    await patients_service.get_patient_for_user(db, session.patient_id, user)
    return session


async def build_summary(db: AsyncSession, session: Session) -> dict[str, Any]:
    """LLM `session_summary.md` → SessionSummary (Ilova B); deterministic text when the chain is
    unavailable or the session is too short to summarise. Also fills `mood_self` for the day."""
    import json  # noqa: PLC0415  (local: this function is the companion wave's only edit here)

    from app.ai.chains import get_chains
    from app.ai.prompts.loader import render
    from app.ai.providers.base import ProviderUnavailable
    from app.core.config import get_settings
    from app.modules.exercises.scoring import session_metrics
    from app.modules.patients.models import RedFlag
    from app.modules.sessions.models import ExerciseAttempt
    from app.modules.sessions.schemas import SessionSummary

    messages = await list_messages(db, session.id)
    patient_turns = sum(1 for m in messages if m.role == "patient")
    attempts = list(
        (
            await db.scalars(
                select(ExerciseAttempt).where(ExerciseAttempt.session_id == session.id)
            )
        ).all()
    )
    flags = list((await db.scalars(select(RedFlag).where(RedFlag.session_id == session.id))).all())
    if session.mood_self is None:
        session.mood_self = await patients_service.today_mood_self(db, session.patient_id)
    state = session.state_snapshot or {}
    ended = session.ended_at or datetime.now(UTC)
    started = session.started_at
    if started is not None and started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    if ended.tzinfo is None:
        ended = ended.replace(tzinfo=UTC)
    metrics = {
        "mode": session.mode,
        "duration_min": round((ended - started).total_seconds() / 60, 1) if started else None,
        "messages": len(messages),
        "patient_turns": patient_turns,
        "exercise": session_metrics(
            [
                {
                    "score": a.score,
                    "result": a.result,
                    "cue_level": a.cue_level,
                    "response_ms": a.response_ms,
                }
                for a in attempts
            ]
        ),
        "state": {k: state.get(k) for k in ("engagement", "fatigue", "mood", "distress")},
        "mood_self": session.mood_self,
        "red_flags": [{"category": f.category, "severity": f.severity} for f in flags],
    }
    attention = bool(state.get("distress")) or any(f.severity in ("medium", "high") for f in flags)
    fallback = {
        "caregiver_text": f"Sessiya yakunlandi: {patient_turns} ta javob berildi.",
        "clinician_text": f"mode={session.mode}, messages={len(messages)}, "
        f"attempts={len(attempts)}, flags={len(flags)}",
        "attention_needed": attention,
    }
    if patient_turns < 2 and not attempts:
        return fallback
    role_uz = {"patient": "Bemor", "ai": "NeuroAI", "caregiver": "Parvarishchi", "system": "Tizim"}
    transcript = "\n".join(
        f"{role_uz.get(m.role, m.role)}: {m.text}" for m in messages[-40:] if m.text
    )[:6000]
    try:
        result = await get_chains(get_settings()).llm.call(
            "generate",
            system=render(
                "session_summary",
                transcript=transcript,
                metrics_json=json.dumps(metrics, ensure_ascii=False),
            ),
            messages=[{"role": "user", "content": "Xulosani JSON shaklida yoz."}],
            schema=SessionSummary,
            temperature=0.2,
            timeout_s=20.0,
            tier="fast",
        )
    except ProviderUnavailable:
        return fallback
    data = result.model_dump()
    data["attention_needed"] = bool(data.get("attention_needed")) or attention
    return data


async def end_session(db: AsyncSession, session: Session) -> Session:
    if session.ended_at is None:
        session.ended_at = datetime.now(UTC)
    session.summary = await build_summary(db, session)
    await db.commit()
    await db.refresh(session)
    return session


async def create_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: str,
    modality: str,
    text: str,
    *,
    commit: bool = True,
    **meta: Any,
) -> Message:
    """meta: audio_path, stt_confidence, stt_provider, llm_meta (unknown keys are dropped)."""
    allowed = {"audio_path", "stt_confidence", "stt_provider", "llm_meta"}
    message = Message(
        session_id=session_id,
        role=role,
        modality=modality,
        text=text,
        **{k: v for k, v in meta.items() if k in allowed},
    )
    db.add(message)
    if commit:
        await db.commit()
        await db.refresh(message)
    else:
        await db.flush()
    return message


async def list_messages(db: AsyncSession, session_id: uuid.UUID) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at, Message.id)
    )
    return list((await db.scalars(stmt)).all())


async def get_recent_messages(
    db: AsyncSession, session_id: uuid.UUID, n: int = 12
) -> list[Message]:
    """Last `n` messages in chronological order (LLM context window)."""
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(n)
    )
    return list(reversed((await db.scalars(stmt)).all()))


async def store_face_metrics(
    db: AsyncSession, session_id: uuid.UUID, batch: list[FaceMetricIn]
) -> int:
    for item in batch:
        data = item.model_dump()
        hint = data.pop("expr_hint", None)
        db.add(FaceMetric(session_id=session_id, expr_hint=hint, **data))
    await db.commit()
    return len(batch)


async def store_state(
    db: AsyncSession, session_id: uuid.UUID, state: PatientStateIn
) -> PatientStateOut:
    row = PatientState(session_id=session_id, ts=datetime.now(UTC), **state.model_dump())
    db.add(row)
    session = await db.get(Session, session_id)
    if session is not None:
        session.state_snapshot = state.model_dump()
    await db.commit()
    await db.refresh(row)
    return _state_out(row)


async def latest_state(db: AsyncSession, session_id: uuid.UUID) -> PatientStateOut:
    stmt = (
        select(PatientState)
        .where(PatientState.session_id == session_id)
        .order_by(PatientState.ts.desc())
        .limit(1)
    )
    row = await db.scalar(stmt)
    return _state_out(row) if row else PatientStateOut()


def _state_out(row: PatientState) -> PatientStateOut:
    return PatientStateOut(
        engagement=row.engagement,  # type: ignore[arg-type]
        fatigue=row.fatigue,
        mood=row.mood,  # type: ignore[arg-type]
        mood_conf=row.mood_conf,
        distress=row.distress,
        stt_confidence=row.stt_confidence,
        explain=row.explain or [],
        inputs=row.inputs or {},
        ts=row.ts,
    )
