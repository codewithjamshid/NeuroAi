"""Clinician dashboard aggregates (TZ §8.3, M7). `daily_metrics()` is reused by reports/demo.

All bucketing is done in Python by UTC calendar day so the same code runs on sqlite and Postgres.
Exercise adherence per day = categories with ≥1 attempt / exercise categories planned that day
(active protocol); medication adherence = taken logs / all logs scheduled that day.
"""

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clinician.schemas import (
    AdherenceWeek,
    ClinicianPatientOut,
    ClinicianSessionOut,
    DashboardOut,
    DayMetrics,
)
from app.modules.patients import service as patients_service
from app.modules.patients.models import MoodEntry, Patient, RedFlag
from app.modules.patients.schemas import RedFlagOut
from app.modules.protocols import service as protocols_service
from app.modules.protocols.models import Medication, MedicationLog
from app.modules.sessions.models import (
    ExerciseAttempt,
    ExerciseTemplate,
    FaceMetric,
    Message,
    Session,
    VoiceMetric,
)
from app.modules.users.models import User

WEEK_DAYS = 7


@dataclass
class DayBucket:
    scores: list[float] = field(default_factory=list)
    independent: int = 0
    cues: list[int] = field(default_factory=list)
    fsi: list[float] = field(default_factory=list)
    moods: list[float] = field(default_factory=list)
    valences: list[float] = field(default_factory=list)
    med_taken: int = 0
    med_planned: int = 0
    ex_done: set[str] = field(default_factory=set)
    ex_planned: set[str] = field(default_factory=set)


def today_utc() -> date:
    return datetime.now(UTC).date()


def _utc(value: datetime | None) -> datetime | None:
    """sqlite returns naive datetimes; the API always speaks UTC-aware ISO strings."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _bounds(start: date, end: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(start, time.min, tzinfo=UTC),
        datetime.combine(end + timedelta(days=1), time.min, tzinfo=UTC),
    )


def _mean(values: list[float], digits: int = 3) -> float | None:
    return round(sum(values) / len(values), digits) if values else None


def _pct(num: int, den: int) -> float | None:
    return round(100.0 * num / den, 1) if den else None


def _planned_categories(protocol: Any, day: date) -> set[str]:
    planned: set[str] = set()
    for item in protocol.items if protocol else []:
        if item.kind != "exercise" or not item.category:
            continue
        days = (item.frequency or {}).get("days")
        if days and day.isoweekday() not in days:
            continue
        planned.add(item.category)
    return planned


async def collect_days(
    db: AsyncSession, patient_id: uuid.UUID, start: date, end: date
) -> dict[date, DayBucket]:
    lo, hi = _bounds(start, end)
    buckets: dict[date, DayBucket] = defaultdict(DayBucket)

    category = func.coalesce(ExerciseAttempt.category, ExerciseTemplate.category, "speech")
    attempts = (
        select(
            ExerciseAttempt.created_at,
            category,
            ExerciseAttempt.score,
            ExerciseAttempt.result,
            ExerciseAttempt.cue_level,
        )
        .join(Session, Session.id == ExerciseAttempt.session_id)
        .outerjoin(ExerciseTemplate, ExerciseTemplate.id == ExerciseAttempt.template_id)
        .where(
            Session.patient_id == patient_id,
            ExerciseAttempt.created_at >= lo,
            ExerciseAttempt.created_at < hi,
        )
    )
    for ts, cat, score, result, cue in (await db.execute(attempts)).all():
        b = buckets[ts.date()]
        b.ex_done.add(cat)
        if cat != "speech" or score is None or result == "skipped":
            continue
        b.scores.append(float(score))
        b.cues.append(int(cue or 0))
        if result == "correct" and not cue:
            b.independent += 1

    faces = (
        select(FaceMetric.created_at, FaceMetric.fsi)
        .join(Session, Session.id == FaceMetric.session_id)
        .where(
            Session.patient_id == patient_id,
            FaceMetric.fsi.is_not(None),
            FaceMetric.face_present.is_(True),
            FaceMetric.created_at >= lo,
            FaceMetric.created_at < hi,
        )
    )
    for ts, fsi in (await db.execute(faces)).all():
        buckets[ts.date()].fsi.append(float(fsi))

    moods = select(MoodEntry.ts, MoodEntry.self_score).where(
        MoodEntry.patient_id == patient_id,
        MoodEntry.self_score.is_not(None),
        MoodEntry.ts >= lo,
        MoodEntry.ts < hi,
    )
    for ts, score in (await db.execute(moods)).all():
        buckets[ts.date()].moods.append(float(score))

    valences = (
        select(Message.created_at, VoiceMetric.valence)
        .join(Message, Message.id == VoiceMetric.message_id)
        .join(Session, Session.id == Message.session_id)
        .where(
            Session.patient_id == patient_id,
            VoiceMetric.valence.is_not(None),
            Message.created_at >= lo,
            Message.created_at < hi,
        )
    )
    for ts, valence in (await db.execute(valences)).all():
        buckets[ts.date()].valences.append(float(valence))

    med_logs = (
        select(MedicationLog.scheduled_at, MedicationLog.status)
        .join(Medication, Medication.id == MedicationLog.medication_id)
        .where(
            Medication.patient_id == patient_id,
            MedicationLog.scheduled_at >= lo,
            MedicationLog.scheduled_at < hi,
        )
    )
    for ts, status in (await db.execute(med_logs)).all():
        b = buckets[ts.date()]
        b.med_planned += 1
        if status == "taken":
            b.med_taken += 1

    protocol = await protocols_service.get_active_protocol(db, patient_id)
    day = start
    while day <= end:
        buckets[day].ex_planned = _planned_categories(protocol, day)
        day += timedelta(days=1)
    return dict(buckets)


def _to_metrics(day: date, b: DayBucket) -> DayMetrics:
    planned = len(b.ex_planned)
    done = len(b.ex_done & b.ex_planned) if planned else 0
    return DayMetrics(
        date=day,
        speech_accuracy=_mean(b.scores),
        independence=round(b.independent / len(b.scores), 3) if b.scores else None,
        avg_cue_level=_mean([float(c) for c in b.cues], 2),
        fsi=_mean(b.fsi),
        mood_self=_mean(b.moods, 2),
        valence=_mean(b.valences),
        adherence_exercise=_pct(done, planned),
        adherence_medication=_pct(b.med_taken, b.med_planned),
    )


def _week(buckets: dict[date, DayBucket], end: date) -> AdherenceWeek:
    ex_done = ex_planned = med_taken = med_planned = 0
    for offset in range(WEEK_DAYS):
        b = buckets.get(end - timedelta(days=offset))
        if b is None:
            continue
        ex_planned += len(b.ex_planned)
        ex_done += len(b.ex_done & b.ex_planned)
        med_taken += b.med_taken
        med_planned += b.med_planned
    return AdherenceWeek(
        exercise=_pct(ex_done, ex_planned), medication=_pct(med_taken, med_planned)
    )


async def daily_metrics(
    db: AsyncSession, patient_id: uuid.UUID, days: int, end: date | None = None
) -> list[DayMetrics]:
    end = end or today_utc()
    start = end - timedelta(days=days - 1)
    buckets = await collect_days(db, patient_id, start, end)
    return [_to_metrics(d, buckets[d]) for d in sorted(buckets) if start <= d <= end]


async def week_adherence(
    db: AsyncSession, patient_id: uuid.UUID, end: date | None = None
) -> AdherenceWeek:
    end = end or today_utc()
    start = end - timedelta(days=WEEK_DAYS - 1)
    return _week(await collect_days(db, patient_id, start, end), end)


async def dashboard(db: AsyncSession, patient: Patient, days: int) -> DashboardOut:
    end = today_utc()
    start = end - timedelta(days=days - 1)
    lo, hi = _bounds(start, end)
    buckets = await collect_days(db, patient.id, start, end)
    rows = [_to_metrics(d, buckets[d]) for d in sorted(buckets) if start <= d <= end]
    fsi_base = next((r.fsi for r in rows if r.fsi is not None), None)
    flags_stmt = (
        select(RedFlag)
        .where(RedFlag.patient_id == patient.id, RedFlag.created_at >= lo)
        .order_by(RedFlag.created_at.desc())
        .limit(50)
    )
    flags = [RedFlagOut.model_validate(f) for f in (await db.scalars(flags_stmt)).all()]
    count_stmt = select(func.count(Session.id)).where(
        Session.patient_id == patient.id, Session.started_at >= lo, Session.started_at < hi
    )
    # the week figure always spans 7 days, even when the chart window is shorter
    week = _week(buckets, end) if days >= WEEK_DAYS else await week_adherence(db, patient.id, end)
    return DashboardOut(
        days=rows,
        flags=flags,
        adherence_week=week,
        sessions_count=int(await db.scalar(count_stmt) or 0),
        fsi_base=fsi_base,
    )


async def list_patients(db: AsyncSession, user: User) -> list[ClinicianPatientOut]:
    year = today_utc().year
    out: list[ClinicianPatientOut] = []
    for p in await patients_service.list_patients(db, user):
        last = await db.scalar(
            select(func.max(Session.started_at)).where(Session.patient_id == p.id)
        )
        out.append(
            ClinicianPatientOut(
                id=p.id,
                full_name=p.full_name,
                age=(year - p.birth_year) if p.birth_year else None,
                aphasia_type=p.aphasia_type,
                open_flags=await patients_service.count_open_flags(db, p.id),
                last_activity=_utc(last),
                adherence_week=(await week_adherence(db, p.id)).exercise,
            )
        )
    return out


async def list_sessions(
    db: AsyncSession, patient: Patient, limit: int, offset: int = 0
) -> list[ClinicianSessionOut]:
    stmt = (
        select(Session)
        .where(Session.patient_id == patient.id)
        .order_by(Session.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    sessions = list((await db.scalars(stmt)).all())
    stats: dict[uuid.UUID, tuple[float | None, int]] = {}
    if sessions:
        agg = (
            select(
                ExerciseAttempt.session_id,
                func.avg(ExerciseAttempt.score),
                func.count(ExerciseAttempt.id),
            )
            .where(ExerciseAttempt.session_id.in_([s.id for s in sessions]))
            .group_by(ExerciseAttempt.session_id)
        )
        for sid, avg, n in (await db.execute(agg)).all():
            stats[sid] = (round(float(avg), 3) if avg is not None else None, int(n))
    return [
        ClinicianSessionOut(
            id=s.id,
            mode=s.mode,
            started_at=_utc(s.started_at),  # type: ignore[arg-type]
            ended_at=_utc(s.ended_at),
            summary=s.summary,
            accuracy=stats.get(s.id, (None, 0))[0],
            attempts=stats.get(s.id, (None, 0))[1],
        )
        for s in sessions
    ]
