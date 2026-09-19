"""Session plan (TZ §7.5): protocol category/subtypes → current level → not shown in the last
3 days → failed items ≥ 2 days old come back first. Stored in sessions.state_snapshot."""

import copy
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.models import Patient, PatientLevel
from app.modules.protocols import service as protocols_service
from app.modules.sessions.models import ExerciseAttempt, ExerciseTemplate, Session
from app.seeds import load_seed

PLAN_SIZE = 8
RECENT_DAYS = 3
RETRY_DAYS = 2
HISTORY_DAYS = 14
CATEGORY = "speech"
SPEECH_SUBTYPES = ["naming", "repetition", "completion", "automatic", "reading"]
FAILED = {"incorrect", "skipped"}


class TemplateLike(Protocol):
    key: str | None
    subtype: str
    level: int


def _round_robin(
    queues: dict[str, list[str]], order: list[str], chosen: list[str], size: int
) -> None:
    while len(chosen) < size and any(queues.values()):
        for subtype in order:
            queue = queues[subtype]
            while queue and queue[0] in chosen:
                queue.pop(0)
            if queue and len(chosen) < size:
                chosen.append(queue.pop(0))


def select_items(
    templates: list[Any],
    subtypes: list[str],
    level: int,
    recent_keys: set[str],
    failed_old_keys: list[str],
    size: int = PLAN_SIZE,
) -> list[str]:
    """Pure selection: failed-old first; then, per level tier (same level, then easier, then
    harder), a subtype round-robin of fresh items; recent items fill the tail if needed."""
    wanted = subtypes or SPEECH_SUBTYPES
    pool = [t for t in templates if t.key and t.subtype in wanted]
    by_key = {t.key: t for t in pool}
    chosen: list[str] = []
    for key in failed_old_keys:
        if key in by_key and abs(by_key[key].level - level) <= 1 and len(chosen) < size:
            chosen.append(key)

    def tier(t: Any) -> tuple[int, int]:
        return abs(t.level - level), 1 if t.level > level else 0

    tiers = sorted({tier(t) for t in pool})
    for fresh_only in (True, False):
        for current in tiers:
            queues = {
                s: [
                    t.key
                    for t in pool
                    if t.subtype == s
                    and tier(t) == current
                    and t.key not in chosen
                    and (not fresh_only or t.key not in recent_keys)
                ]
                for s in wanted
            }
            _round_robin(queues, wanted, chosen, size)
            if len(chosen) >= size:
                return chosen[:size]
    return chosen[:size]


async def ensure_templates(db: AsyncSession) -> list[ExerciseTemplate]:
    """Active speech templates in seed order; imports exercises_uz.json if the table is empty."""
    stmt = select(ExerciseTemplate).where(
        ExerciseTemplate.active.is_(True), ExerciseTemplate.category == CATEGORY
    )
    rows = list((await db.scalars(stmt)).all())
    if not rows:
        for item in load_seed("exercises_uz"):
            db.add(
                ExerciseTemplate(
                    key=item["key"],
                    category=item.get("category", CATEGORY),
                    subtype=item["subtype"],
                    level=int(item.get("level", 1)),
                    prompt_text=item["prompt_text"],
                    stimulus=item.get("stimulus"),
                    expected=item.get("expected"),
                    cues=item.get("cues"),
                    tags=item.get("tags"),
                )
            )
        await db.commit()
        rows = list((await db.scalars(stmt)).all())
    seed_order = {item["key"]: i for i, item in enumerate(load_seed("exercises_uz"))}
    rows.sort(key=lambda t: seed_order.get(t.key or "", len(seed_order)))
    return rows


async def current_level(db: AsyncSession, patient_id: uuid.UUID, category: str) -> int | None:
    stmt = select(PatientLevel.level).where(
        PatientLevel.patient_id == patient_id, PatientLevel.category == category
    )
    return await db.scalar(stmt)


async def attempt_history(
    db: AsyncSession, patient_id: uuid.UUID, now: datetime | None = None
) -> tuple[set[str], list[str]]:
    """→ (keys attempted in the last 3 days, failed keys whose last attempt is ≥ 2 days old)."""
    now = now or datetime.now(UTC)
    stmt = (
        select(ExerciseTemplate.key, ExerciseAttempt.result, ExerciseAttempt.created_at)
        .join(Session, Session.id == ExerciseAttempt.session_id)
        .join(ExerciseTemplate, ExerciseTemplate.id == ExerciseAttempt.template_id)
        .where(
            Session.patient_id == patient_id,
            ExerciseAttempt.created_at >= now - timedelta(days=HISTORY_DAYS),
        )
        .order_by(ExerciseAttempt.created_at)
    )
    last: dict[str, tuple[datetime, str | None]] = {}
    for key, result, created in (await db.execute(stmt)).all():
        if key:
            last[key] = (created, result)
    recent = {k for k, (ts, _) in last.items() if ts >= now - timedelta(days=RECENT_DAYS)}
    failed_old = sorted(
        (
            k
            for k, (ts, r) in last.items()
            if r in FAILED and ts <= now - timedelta(days=RETRY_DAYS)
        ),
        key=lambda k: last[k][0],
    )
    return recent, failed_old


async def build_plan(db: AsyncSession, patient: Patient) -> dict[str, Any]:
    protocol = await protocols_service.get_active_protocol(db, patient.id)
    subtypes: list[str] = []
    item_level: int | None = None
    for item in protocol.items if protocol else []:
        if item.kind != "exercise" or item.category != CATEGORY:
            continue
        for s in (item.params or {}).get("subtypes") or []:
            if s not in subtypes:
                subtypes.append(s)
        item_level = item_level or item.level
    level = await current_level(db, patient.id, CATEGORY) or item_level or 1
    templates = await ensure_templates(db)
    recent, failed_old = await attempt_history(db, patient.id)
    keys = select_items(templates, subtypes, level, recent, failed_old)
    return {
        "category": CATEGORY,
        "subtypes": subtypes or SPEECH_SUBTYPES,
        "level": level,
        "keys": keys,
        "index": 0,
        "attempt_id": None,
        "streak_from": 0,
        "built_at": datetime.now(UTC).isoformat(),
    }


def save_plan(session: Session, plan: dict[str, Any]) -> None:
    """Copies so the JSON column's committed value is never mutated in place (change detection)."""
    snapshot = {**(session.state_snapshot or {}), "exercise_plan": copy.deepcopy(plan)}
    session.state_snapshot = snapshot


def get_plan(session: Session) -> dict[str, Any] | None:
    plan = (session.state_snapshot or {}).get("exercise_plan")
    return copy.deepcopy(plan) if plan else None
