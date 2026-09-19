"""Idempotent demo seed (`make seed`, TZ Ilova C): 3 demo users, Bobur's card, caregiver link,
consent, patient levels, active protocol from `motor_aphasia_m1` (if templates JSON exists) and
exercise templates from `app/seeds/exercises_uz.json` (if it exists). Requires `make migrate`."""

import asyncio
import hashlib
import json
import logging
import sys
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # `python scripts/seed.py` (make seed)

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

import app.db.registry  # noqa: F401, E402
from app.core.config import API_DIR  # noqa: E402
from app.db.session import dispose_engine, get_sessionmaker  # noqa: E402
from app.modules.auth.security import hash_password  # noqa: E402
from app.modules.patients.models import Caregiver, Consent, Patient, PatientLevel  # noqa: E402
from app.modules.protocols import service as protocols_service  # noqa: E402
from app.modules.protocols.schemas import ProtocolCreate  # noqa: E402
from app.modules.sessions.models import ExerciseTemplate  # noqa: E402
from app.modules.users.models import User  # noqa: E402

log = logging.getLogger("neuroai.seed")

DEMO_PASSWORD = "demo1234"
DEMO_PIN = "1234"
DEMO_TEMPLATE_KEY = "motor_aphasia_m1"
EXERCISES_PATH: Path = API_DIR / "app" / "seeds" / "exercises_uz.json"

DEMO_USERS = [
    {"email": "logoped@demo.uz", "role": "clinician", "full_name": "Dilnoza Karimova"},
    {"email": "qizi@demo.uz", "role": "caregiver", "full_name": "Nilufar"},
    {"email": "bemor@demo.uz", "role": "patient", "full_name": "Bobur Matnazarov"},
]

DEMO_PATIENT = {
    "full_name": "Bobur Matnazarov",
    "birth_year": 1964,
    "sex": "male",
    "stroke_date": date(2026, 8, 5),
    "stroke_type": "ischemic",
    "affected_side": "left",
    "aphasia_type": "motor",
    "dysarthria": False,
    "facial_palsy_side": "left",
    "dominant_hand": "right",
    "dialect": "khorezm",
    "interests": ["bog'dorchilik", "futbol", "nabiralar"],
    "family_members": [
        {"name": "Nilufar", "relation": "qizi"},
        {"name": "Sardor", "relation": "o'g'li"},
        {"name": "Hurmat", "relation": "turmush o'rtog'i"},
    ],
    "habits": ["soat 7 da choy ichadi", "kechqurun futbol ko'radi"],
    "notes": "Urganch. Demo bemor (TZ Ilova C).",
}


async def _ensure_users(db: AsyncSession) -> tuple[dict[str, User], int]:
    users: dict[str, User] = {}
    created = 0
    for spec in DEMO_USERS:
        user = await db.scalar(select(User).where(User.email == spec["email"]))
        if user is None:
            user = User(**spec, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            created += 1
        users[spec["role"]] = user
    await db.flush()
    return users, created


async def _ensure_patient(db: AsyncSession, users: dict[str, User]) -> tuple[Patient, int]:
    patient_user = users["patient"]
    patient = await db.scalar(select(Patient).where(Patient.user_id == patient_user.id))
    if patient is not None:
        return patient, 0
    patient = Patient(
        user_id=patient_user.id,
        clinician_id=users["clinician"].id,
        pin_hash=hash_password(DEMO_PIN),
        **DEMO_PATIENT,
    )
    db.add(patient)
    await db.flush()
    return patient, 1


async def _ensure_links(db: AsyncSession, users: dict[str, User], patient: Patient) -> None:
    caregiver = users["caregiver"]
    link = await db.scalar(
        select(Caregiver).where(
            Caregiver.user_id == caregiver.id, Caregiver.patient_id == patient.id
        )
    )
    if link is None:
        db.add(
            Caregiver(
                user_id=caregiver.id, patient_id=patient.id, relation="daughter", is_primary=True
            )
        )
    if patient.consent_id is None:
        consent = Consent(
            patient_id=patient.id,
            signed_by=caregiver.id,
            version="1.0",
            scopes={"audio_retention": True, "data_for_research": False, "clinician_view": True},
            signed_at=datetime.now(UTC),
        )
        db.add(consent)
        await db.flush()
        patient.consent_id = consent.id
    for category in ("speech", "face", "cognitive"):
        exists = await db.scalar(
            select(PatientLevel.id).where(
                PatientLevel.patient_id == patient.id, PatientLevel.category == category
            )
        )
        if exists is None:
            db.add(PatientLevel(patient_id=patient.id, category=category, level=1))
    await db.flush()


async def _ensure_protocol(
    db: AsyncSession, users: dict[str, User], patient: Patient, templates_path: Path | None
) -> int:
    if await protocols_service.get_active_protocol(db, patient.id) is not None:
        return 0
    keys = {t.key for t in protocols_service.load_templates(templates_path)}
    if DEMO_TEMPLATE_KEY not in keys:
        log.warning("protocol template missing, skipped", extra={"key": DEMO_TEMPLATE_KEY})
        print(f"seed: '{DEMO_TEMPLATE_KEY}' shabloni topilmadi — protokol o'tkazib yuborildi")
        return 0
    await protocols_service.create_protocol(
        db,
        patient,
        users["clinician"],
        ProtocolCreate(template_key=DEMO_TEMPLATE_KEY),
        templates_path=templates_path,
    )
    return 1


def exercise_key(item: dict) -> str:
    """Seed `key` if present, else a stable hash of (subtype, level, prompt, stimulus, expected)."""
    if item.get("key"):
        return str(item["key"])[:64]
    level = item.get("level", 1)
    payload = json.dumps(
        [item["subtype"], level, item["prompt_text"], item.get("stimulus"), item.get("expected")],
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha1(payload.encode()).hexdigest()[:10]
    return f"{item['subtype']}_l{level}_{digest}"


async def import_exercises(db: AsyncSession, path: Path | None = None) -> int:
    """Upsert exercise templates by natural key (`key` in the JSON). Returns rows inserted."""
    file = path or EXERCISES_PATH
    if not file.exists():
        print(f"seed: {file.name} topilmadi — mashqlar o'tkazib yuborildi")
        return 0
    raw = json.loads(file.read_text(encoding="utf-8"))
    items = raw.get("items", raw.get("exercises", [])) if isinstance(raw, dict) else raw
    existing = set((await db.scalars(select(ExerciseTemplate.key))).all())
    inserted = 0
    for item in items:
        key = exercise_key(item)
        if key in existing:
            continue
        existing.add(key)
        db.add(
            ExerciseTemplate(
                key=key,
                category=item.get("category", "speech"),
                subtype=item["subtype"],
                prompt_text=item["prompt_text"],
                level=int(item.get("level", 1)),
                prompt_tts_path=item.get("prompt_tts_path"),
                stimulus=item.get("stimulus"),
                expected=item.get("expected"),
                cues=item.get("cues"),
                tags=item.get("tags"),
                lang=item.get("lang", "uz-Latn"),
                active=item.get("active", True),
            )
        )
        inserted += 1
    await db.flush()
    return inserted


async def seed(
    db: AsyncSession, templates_path: Path | None = None, exercises_path: Path | None = None
) -> dict[str, int]:
    users, users_created = await _ensure_users(db)
    patient, patients_created = await _ensure_patient(db, users)
    await _ensure_links(db, users, patient)
    protocols_created = await _ensure_protocol(db, users, patient, templates_path)
    exercises_inserted = await import_exercises(db, exercises_path)
    await db.commit()
    return {
        "users_created": users_created,
        "patients_created": patients_created,
        "protocols_created": protocols_created,
        "exercises_inserted": exercises_inserted,
    }


async def _run() -> dict[str, int]:
    async with get_sessionmaker()() as db:
        result = await seed(db)
    await dispose_engine()
    return result


def main() -> int:
    result = asyncio.run(_run())
    print("seed:", json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
