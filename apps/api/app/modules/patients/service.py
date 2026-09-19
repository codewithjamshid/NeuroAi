"""Patient cards, consent, mood, red flags. Access: clinician → own patients, caregiver →
linked, patient → self, admin → all (`get_patient_for_user` is reused by other modules)."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.models import Caregiver, Consent, MoodEntry, Patient, RedFlag
from app.modules.patients.schemas import (
    ConsentIn,
    MoodTrendPoint,
    PatientCreate,
    PatientPatch,
    RedFlagPatch,
)
from app.modules.users.errors import ForbiddenError, NotFoundError
from app.modules.users.models import AuditLog, User

CLINICIAN_ONLY_FIELDS = {"aphasia_type", "clinician_id"}


async def has_access(db: AsyncSession, patient: Patient, user: User) -> bool:
    if user.role == "admin":
        return True
    if user.role == "clinician":
        return patient.clinician_id == user.id
    if user.role == "patient":
        return patient.user_id == user.id
    if user.role == "caregiver":
        stmt = select(Caregiver.id).where(
            Caregiver.user_id == user.id, Caregiver.patient_id == patient.id
        )
        return (await db.scalar(stmt)) is not None
    return False


async def get_patient_for_user(db: AsyncSession, patient_id: uuid.UUID, user: User) -> Patient:
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise NotFoundError("Bemor topilmadi")
    if not await has_access(db, patient, user):
        raise ForbiddenError("Bu bemorga ruxsat yo'q")
    return patient


async def list_patients(db: AsyncSession, user: User) -> list[Patient]:
    stmt = select(Patient).order_by(Patient.created_at)
    if user.role == "clinician":
        stmt = stmt.where(Patient.clinician_id == user.id)
    elif user.role == "caregiver":
        stmt = stmt.join(Caregiver, Caregiver.patient_id == Patient.id).where(
            Caregiver.user_id == user.id
        )
    elif user.role == "patient":
        stmt = stmt.where(Patient.user_id == user.id)
    return list((await db.scalars(stmt)).all())


async def create_patient(db: AsyncSession, user: User, data: PatientCreate) -> Patient:
    fields = data.model_dump(exclude={"consent", "caregiver_relation", "clinician_id"})
    if user.role == "caregiver":
        fields.pop("aphasia_type", None)  # only a clinician sets the diagnosis
    patient = Patient(**fields)
    patient.clinician_id = user.id if user.role == "clinician" else data.clinician_id
    db.add(patient)
    await db.flush()
    if user.role == "caregiver":
        db.add(
            Caregiver(
                user_id=user.id,
                patient_id=patient.id,
                relation=data.caregiver_relation,
                is_primary=True,
            )
        )
    if data.consent is not None:
        await _add_consent(db, patient, user, data.consent)
    await db.commit()
    await db.refresh(patient)
    return patient


async def update_patient(
    db: AsyncSession, patient: Patient, user: User, data: PatientPatch
) -> Patient:
    fields = data.model_dump(exclude_unset=True)
    if user.role not in ("clinician", "admin"):
        for key in CLINICIAN_ONLY_FIELDS:
            fields.pop(key, None)
    for key, value in fields.items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return patient


async def _add_consent(db: AsyncSession, patient: Patient, user: User, data: ConsentIn) -> Consent:
    consent = Consent(
        patient_id=patient.id,
        signed_by=user.id,
        version=data.version,
        scopes=data.scopes,
        signed_at=datetime.now(UTC),
    )
    db.add(consent)
    await db.flush()
    patient.consent_id = consent.id
    return consent


async def add_consent(db: AsyncSession, patient: Patient, user: User, data: ConsentIn) -> Consent:
    consent = await _add_consent(db, patient, user, data)
    await db.commit()
    await db.refresh(consent)
    return consent


async def add_mood(db: AsyncSession, patient: Patient, user: User, self_score: int) -> MoodEntry:
    source = "patient" if user.role == "patient" else "caregiver"
    entry = MoodEntry(
        patient_id=patient.id, ts=datetime.now(UTC), self_score=self_score, source=source
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def mood_trend(db: AsyncSession, patient: Patient, days: int) -> list[MoodTrendPoint]:
    since = datetime.now(UTC) - timedelta(days=days)
    stmt = (
        select(MoodEntry.ts, MoodEntry.self_score, MoodEntry.derived_valence)
        .where(MoodEntry.patient_id == patient.id, MoodEntry.ts >= since)
        .order_by(MoodEntry.ts)
    )
    buckets: dict[date, dict[str, list[float]]] = {}
    for ts, score, valence in (await db.execute(stmt)).all():
        bucket = buckets.setdefault(ts.date(), {"score": [], "valence": []})
        if score is not None:
            bucket["score"].append(float(score))
        if valence is not None:
            bucket["valence"].append(float(valence))
    return [
        MoodTrendPoint(
            date=day,
            self_score=_avg(values["score"]),
            valence=_avg(values["valence"]),
        )
        for day, values in sorted(buckets.items())
    ]


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


async def today_mood_self(db: AsyncSession, patient_id: uuid.UUID) -> int | None:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = (
        select(MoodEntry.self_score)
        .where(
            MoodEntry.patient_id == patient_id,
            MoodEntry.ts >= start,
            MoodEntry.self_score.is_not(None),
        )
        .order_by(MoodEntry.ts.desc())
        .limit(1)
    )
    return await db.scalar(stmt)


async def list_red_flags(
    db: AsyncSession, patient: Patient, status: str | None, limit: int, offset: int
) -> list[RedFlag]:
    stmt = select(RedFlag).where(RedFlag.patient_id == patient.id)
    if status:
        stmt = stmt.where(RedFlag.status == status)
    stmt = stmt.order_by(RedFlag.created_at.desc()).limit(limit).offset(offset)
    return list((await db.scalars(stmt)).all())


async def update_red_flag(
    db: AsyncSession, flag_id: uuid.UUID, user: User, data: RedFlagPatch
) -> RedFlag:
    flag = await db.get(RedFlag, flag_id)
    if flag is None:
        raise NotFoundError("Bayroq topilmadi")
    await get_patient_for_user(db, flag.patient_id, user)
    previous = flag.status
    flag.status = data.status
    if data.note is not None:
        flag.note = data.note
    db.add(
        AuditLog(
            actor_id=user.id,
            action="red_flag.status",
            entity="red_flags",
            entity_id=flag.id,
            meta={"from": previous, "to": data.status, "note": data.note},
        )
    )
    await db.commit()
    await db.refresh(flag)
    return flag


async def count_open_flags(db: AsyncSession, patient_id: uuid.UUID) -> int:
    stmt = select(func.count(RedFlag.id)).where(
        RedFlag.patient_id == patient_id, RedFlag.status == "open"
    )
    return int(await db.scalar(stmt) or 0)
