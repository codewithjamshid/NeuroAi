"""scripts/seed.py is idempotent (run twice → no duplicates) and imports exercises when present."""

import json
from pathlib import Path

from sqlalchemy import func, select

from core.conftest import TEMPLATES

EXERCISES = [
    {
        "category": "speech",
        "subtype": "naming",
        "level": 1,
        "prompt_text": "Bu nima?",
        "stimulus": {"emoji": "🍵"},
        "expected": {"answers": ["choy", "чой"]},
        "cues": {"semantic": "Bu ichiladi.", "phonemic": "cho…"},
        "tags": ["food"],
    },
    {
        "category": "face",
        "subtype": "face_smile",
        "level": 1,
        "prompt_text": "Keng tabassum qiling",
    },
]


async def _counts() -> dict[str, int]:
    from app.db.session import get_sessionmaker
    from app.modules.patients.models import Caregiver, Consent, Patient, PatientLevel
    from app.modules.protocols.models import Protocol, ProtocolItem
    from app.modules.sessions.models import ExerciseTemplate
    from app.modules.users.models import User

    tables = {
        "users": User,
        "patients": Patient,
        "caregivers": Caregiver,
        "consents": Consent,
        "levels": PatientLevel,
        "protocols": Protocol,
        "items": ProtocolItem,
        "exercises": ExerciseTemplate,
    }
    async with get_sessionmaker()() as db:
        return {
            name: int(await db.scalar(select(func.count(model.id))) or 0)
            for name, model in tables.items()
        }


async def test_seed_twice_is_idempotent(db_ready: None, tmp_path: Path) -> None:
    from app.db.session import get_sessionmaker
    from scripts.seed import seed

    exercises = tmp_path / "exercises_uz.json"
    exercises.write_text(json.dumps(EXERCISES, ensure_ascii=False), encoding="utf-8")

    async with get_sessionmaker()() as db:
        first = await seed(db, templates_path=TEMPLATES, exercises_path=exercises)
    assert first == {
        "users_created": 3,
        "patients_created": 1,
        "protocols_created": 1,
        "exercises_inserted": 2,
    }
    expected = {
        "users": 3,
        "patients": 1,
        "caregivers": 1,
        "consents": 1,
        "levels": 3,
        "protocols": 1,
        "items": 4,
        "exercises": 2,
    }
    assert await _counts() == expected

    async with get_sessionmaker()() as db:
        second = await seed(db, templates_path=TEMPLATES, exercises_path=exercises)
    assert second == {
        "users_created": 0,
        "patients_created": 0,
        "protocols_created": 0,
        "exercises_inserted": 0,
    }
    assert await _counts() == expected


async def test_seed_without_templates_or_exercises(db_ready: None, tmp_path: Path) -> None:
    from app.db.session import get_sessionmaker
    from scripts.seed import seed

    async with get_sessionmaker()() as db:
        result = await seed(
            db, templates_path=tmp_path / "none.json", exercises_path=tmp_path / "x.json"
        )
    assert result["protocols_created"] == 0 and result["exercises_inserted"] == 0
    counts = await _counts()
    assert counts["users"] == 3 and counts["protocols"] == 0 and counts["levels"] == 3
