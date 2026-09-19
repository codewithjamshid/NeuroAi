"""Protocol templates (JSON seed), protocols/items, medications, and the daily plan (M6)."""

import json
import logging
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import API_DIR
from app.modules.patients import service as patients_service
from app.modules.patients.models import Patient, PatientLevel
from app.modules.protocols.models import Medication, MedicationLog, Protocol, ProtocolItem
from app.modules.protocols.schemas import (
    ItemIn,
    ItemPatch,
    MedicationIn,
    MedLogIn,
    ProtocolCreate,
    ProtocolPatch,
    TemplateOut,
    TodayItem,
    TodayOut,
)
from app.modules.sessions.models import ExerciseAttempt, ExerciseTemplate, Session
from app.modules.users.errors import NotFoundError
from app.modules.users.models import User

log = logging.getLogger(__name__)

# Written by the content agent; tests/seed may point elsewhere (monkeypatch or `path=` arg).
TEMPLATES_PATH: Path = API_DIR / "app" / "seeds" / "protocol_templates.json"

TITLES = {
    "speech": "Nutq mashqi",
    "face": "Yuz mashqi",
    "cognitive": "Kognitiv mashq",
    "hand": "Qo'l mashqi",
    "mood": "Kayfiyat so'rovi",
    "checkin": "Kayfiyat so'rovi",
}


# --- templates -------------------------------------------------------------------------------


def load_templates(path: Path | None = None) -> list[TemplateOut]:
    file = path or TEMPLATES_PATH
    if not file.exists():
        log.warning("protocol templates missing", extra={"path": str(file)})
        return []
    raw = json.loads(file.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("templates") or [{"key": k, **v} for k, v in raw.items()]
    return [TemplateOut.model_validate(t) for t in raw]


def get_template(key: str, path: Path | None = None) -> TemplateOut:
    for template in load_templates(path):
        if template.key == key:
            return template
    raise NotFoundError("Shablon topilmadi", code="template_not_found")


# --- protocols -------------------------------------------------------------------------------


async def get_active_protocol(db: AsyncSession, patient_id: uuid.UUID) -> Protocol | None:
    stmt = (
        select(Protocol)
        .where(Protocol.patient_id == patient_id, Protocol.status == "active")
        .order_by(Protocol.created_at.desc())
        .limit(1)
    )
    return await db.scalar(stmt)


async def get_protocol(db: AsyncSession, protocol_id: uuid.UUID) -> Protocol:
    protocol = await db.get(Protocol, protocol_id)
    if protocol is None:
        raise NotFoundError("Protokol topilmadi")
    return protocol


async def _pause_active(db: AsyncSession, patient_id: uuid.UUID, keep: uuid.UUID | None) -> None:
    stmt = select(Protocol).where(Protocol.patient_id == patient_id, Protocol.status == "active")
    for other in (await db.scalars(stmt)).all():
        if other.id != keep:
            other.status = "paused"


async def _seed_levels(db: AsyncSession, patient_id: uuid.UUID, items: list[ItemIn]) -> None:
    for item in items:
        if item.kind != "exercise" or not item.category:
            continue
        stmt = select(PatientLevel).where(
            PatientLevel.patient_id == patient_id, PatientLevel.category == item.category
        )
        level = await db.scalar(stmt)
        if level is None:
            db.add(
                PatientLevel(patient_id=patient_id, category=item.category, level=item.level or 1)
            )
        elif not level.locked_by_clinician and item.level:
            level.level = item.level


async def create_protocol(
    db: AsyncSession,
    patient: Patient,
    user: User,
    data: ProtocolCreate,
    templates_path: Path | None = None,
) -> Protocol:
    title = data.title
    items = data.items
    if data.template_key:
        template = get_template(data.template_key, templates_path)
        title = title or template.title
        if items is None:
            items = [ItemIn(**t.model_dump()) for t in template.items]
    items = items or []
    await _pause_active(db, patient.id, keep=None)
    protocol = Protocol(
        patient_id=patient.id,
        clinician_id=user.id if user.role == "clinician" else patient.clinician_id,
        title=title or "Reabilitatsiya protokoli",
        template_key=data.template_key,
        start_date=data.start_date or date.today(),
        status="active",
        notes=data.notes,
    )
    db.add(protocol)
    await db.flush()
    for item in items:
        db.add(_item_from_in(protocol.id, item))
    await _seed_levels(db, patient.id, items)
    await db.commit()
    return await _reload(db, protocol.id)


def _item_from_in(protocol_id: uuid.UUID, item: ItemIn) -> ProtocolItem:
    return ProtocolItem(
        protocol_id=protocol_id,
        kind=item.kind,
        category=item.category,
        level=item.level,
        frequency=item.frequency.model_dump(exclude_none=True),
        duration_min=item.duration_min,
        params=_params_with_title(item.params, item.title),
        medication_id=item.medication_id,
    )


def _params_with_title(params: dict[str, Any] | None, title: str | None) -> dict[str, Any] | None:
    if title is None:
        return params
    return {**(params or {}), "title": title}


async def _reload(db: AsyncSession, protocol_id: uuid.UUID) -> Protocol:
    db.expire_all()
    return await get_protocol(db, protocol_id)


async def update_protocol(db: AsyncSession, protocol: Protocol, data: ProtocolPatch) -> Protocol:
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(protocol, key, value)
    if fields.get("status") == "active":
        await _pause_active(db, protocol.patient_id, keep=protocol.id)
    await db.commit()
    return await _reload(db, protocol.id)


async def add_item(db: AsyncSession, protocol: Protocol, data: ItemIn) -> ProtocolItem:
    item = _item_from_in(protocol.id, data)
    db.add(item)
    await _seed_levels(db, protocol.patient_id, [data])
    await db.commit()
    await db.refresh(item)
    return item


async def get_item(db: AsyncSession, item_id: uuid.UUID) -> ProtocolItem:
    item = await db.get(ProtocolItem, item_id)
    if item is None:
        raise NotFoundError("Protokol elementi topilmadi")
    return item


async def update_item(db: AsyncSession, item: ProtocolItem, data: ItemPatch) -> ProtocolItem:
    fields = data.model_dump(exclude_unset=True)
    if "frequency" in fields and data.frequency is not None:
        fields["frequency"] = data.frequency.model_dump(exclude_none=True)
    if fields.pop("title", None) is not None:
        fields["params"] = _params_with_title(fields.get("params", item.params), data.title)
    for key, value in fields.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: ProtocolItem) -> None:
    await db.delete(item)
    await db.commit()


# --- medications -----------------------------------------------------------------------------


async def list_medications(db: AsyncSession, patient_id: uuid.UUID) -> list[Medication]:
    stmt = (
        select(Medication)
        .where(Medication.patient_id == patient_id)
        .order_by(Medication.created_at)
    )
    return list((await db.scalars(stmt)).all())


async def add_medication(db: AsyncSession, patient_id: uuid.UUID, data: MedicationIn) -> Medication:
    med = Medication(patient_id=patient_id, **data.model_dump())
    db.add(med)
    await db.commit()
    await db.refresh(med)
    return med


async def get_medication(db: AsyncSession, medication_id: uuid.UUID) -> Medication:
    med = await db.get(Medication, medication_id)
    if med is None:
        raise NotFoundError("Dori topilmadi")
    return med


async def log_medication(
    db: AsyncSession, med: Medication, user: User, data: MedLogIn
) -> MedicationLog:
    now = datetime.now(UTC)
    entry = MedicationLog(
        medication_id=med.id,
        scheduled_at=data.scheduled_at or now,
        taken_at=data.taken_at or (now if data.status == "taken" else None),
        status=data.status,
        source="patient" if user.role == "patient" else "caregiver",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


# --- today -----------------------------------------------------------------------------------


def _day_start() -> datetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


async def _exercise_sessions_done_today(db: AsyncSession, patient_id: uuid.UUID) -> dict[str, int]:
    """category → number of distinct sessions today with ≥1 attempt in that category."""
    category = func.coalesce(ExerciseAttempt.category, ExerciseTemplate.category)
    stmt = (
        select(category, func.count(func.distinct(ExerciseAttempt.session_id)))
        .select_from(ExerciseAttempt)
        .join(Session, Session.id == ExerciseAttempt.session_id)
        .outerjoin(ExerciseTemplate, ExerciseTemplate.id == ExerciseAttempt.template_id)
        .where(Session.patient_id == patient_id, Session.started_at >= _day_start())
        .group_by(category)
    )
    return {cat: int(n) for cat, n in (await db.execute(stmt)).all() if cat}


async def _medication_taken_today(db: AsyncSession, patient_id: uuid.UUID) -> dict[uuid.UUID, int]:
    stmt = (
        select(MedicationLog.medication_id, func.count(MedicationLog.id))
        .join(Medication, Medication.id == MedicationLog.medication_id)
        .where(
            Medication.patient_id == patient_id,
            MedicationLog.status == "taken",
            MedicationLog.created_at >= _day_start(),
        )
        .group_by(MedicationLog.medication_id)
    )
    return {mid: int(n) for mid, n in (await db.execute(stmt)).all()}


def _scheduled_today(frequency: dict[str, Any] | None, today: date) -> tuple[int, list[str]]:
    freq = frequency or {}
    days = freq.get("days")
    if days and today.isoweekday() not in days:
        return 0, []
    times = list(freq.get("times") or [])
    return max(int(freq.get("times_per_day") or 1), len(times)), times


async def build_today(db: AsyncSession, patient: Patient) -> TodayOut:
    today = datetime.now(UTC).date()
    items: list[TodayItem] = []
    protocol = await get_active_protocol(db, patient.id)
    done_exercise = await _exercise_sessions_done_today(db, patient.id)
    mood_self = await patients_service.today_mood_self(db, patient.id)

    for item in protocol.items if protocol else []:
        if item.kind == "medication":
            continue  # medications are listed from the medications table below
        count, times = _scheduled_today(item.frequency, today)
        key = item.category or "checkin"
        for n in range(count):
            done = (
                (n < done_exercise.get(key, 0))
                if item.kind == "exercise"
                else mood_self is not None
            )
            items.append(
                TodayItem(
                    id=f"{item.id}:{n}",
                    kind=item.kind,  # type: ignore[arg-type]
                    title=item.title or TITLES.get(key, key),
                    category=item.category,
                    level=item.level,
                    duration_min=item.duration_min,
                    time=times[n] if n < len(times) else None,
                    done=done,
                    protocol_item_id=item.id,
                )
            )

    taken = await _medication_taken_today(db, patient.id)
    for med in await list_medications(db, patient.id):
        if not med.active:
            continue
        count, times = _scheduled_today(med.schedule, today)
        for n in range(count):
            items.append(
                TodayItem(
                    id=f"{med.id}:{n}",
                    kind="medication",
                    title=f"Dori: {med.name}" + (f" ({med.dose})" if med.dose else ""),
                    time=times[n] if n < len(times) else None,
                    done=n < taken.get(med.id, 0),
                    medication_id=med.id,
                )
            )

    items.sort(key=lambda i: (i.time or "99:99", i.kind))
    return TodayOut(date=today, items=items, mood_self=mood_self)
