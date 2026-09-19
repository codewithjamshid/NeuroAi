"""SafetyService (TZ §6): merge LLM `risk` with keyword hits (higher wins), write/dedup red_flags,
escalate via notifications, swap the reply for a safe script on `high`."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts.safe_scripts_uz import medication_reply, safe_script
from app.core.config import Settings
from app.core.uz_text import normalize
from app.modules.companion.schemas import Risk
from app.modules.notifications import service as notifications_service
from app.modules.patients.models import Caregiver, Patient, RedFlag
from app.modules.safety.keywords_uz import detect
from app.modules.safety.schemas import SafetyOutcome
from app.modules.sessions.models import Session
from app.modules.users.models import User

LEVEL_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}
DEDUP_WINDOW = timedelta(minutes=30)
MEDICATION_WORDS = ("dori", "dorim", "dorini", "tabletka", "dorilar", "дори")


def _mentions_medication(text: str) -> bool:
    norm = " " + normalize(text) + " "
    return any(" " + normalize(w) in norm for w in MEDICATION_WORDS)


def merge_risk(llm_risk: Risk | None, text: str) -> tuple[Risk, str, list[dict]]:
    """→ (risk, detector, keyword hits). Keywords win ties only when the LLM said `none`."""
    hits = detect(text)
    llm = llm_risk or Risk()
    if not hits:
        return llm, "llm", []
    top = hits[0]
    if LEVEL_RANK[top.level] > LEVEL_RANK[llm.level] or llm.category == "none":
        risk = Risk(level=top.level, category=top.category, evidence=llm.evidence or top.evidence)  # type: ignore[arg-type]
        return risk, "keywords", [h.as_dict() for h in hits]
    return llm, "llm", [h.as_dict() for h in hits]


async def caregiver_first_name(db: AsyncSession, patient: Patient) -> str | None:
    stmt = (
        select(User.full_name)
        .join(Caregiver, Caregiver.user_id == User.id)
        .where(Caregiver.patient_id == patient.id)
        .order_by(Caregiver.is_primary.desc(), Caregiver.created_at)
        .limit(1)
    )
    name = await db.scalar(stmt)
    if not name:
        for member in patient.family_members or []:
            if isinstance(member, dict) and member.get("name"):
                return str(member["name"]).split()[0]
        return None
    return str(name).split()[0]


async def find_open_flag(
    db: AsyncSession, patient_id: uuid.UUID, category: str, since: datetime
) -> RedFlag | None:
    stmt = (
        select(RedFlag)
        .where(
            RedFlag.patient_id == patient_id,
            RedFlag.category == category,
            RedFlag.status == "open",
            RedFlag.created_at >= since,
        )
        .order_by(RedFlag.created_at.desc())
        .limit(1)
    )
    return await db.scalar(stmt)


async def upsert_flag(
    db: AsyncSession,
    patient: Patient,
    session: Session | None,
    risk: Risk,
    detector: str,
) -> tuple[RedFlag, bool]:
    now = datetime.now(UTC)
    existing = await find_open_flag(db, patient.id, risk.category, now - DEDUP_WINDOW)
    if existing is not None:
        if LEVEL_RANK[risk.level] > LEVEL_RANK[existing.severity]:
            existing.severity = risk.level
        await db.commit()
        return existing, False
    flag = RedFlag(
        patient_id=patient.id,
        session_id=session.id if session else None,
        category=risk.category,
        severity=risk.level,
        evidence=(risk.evidence or "")[:500] or None,
        detector=detector,
        status="open",
    )
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    return flag, True


class SafetyService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def evaluate(
        self,
        db: AsyncSession,
        *,
        patient: Patient,
        session: Session | None,
        text: str,
        llm_risk: Risk | None,
        intent: str = "",
    ) -> SafetyOutcome:
        risk, detector, hits = merge_risk(llm_risk, text)
        medication = (
            risk.category == "medication"
            or "medic" in intent.lower()
            or "dori" in intent.lower()
            or _mentions_medication(text)
        )
        outcome = SafetyOutcome(
            risk=risk, detector=detector, medication=medication, keyword_hits=hits
        )

        if medication and risk.category in ("none", "medication"):
            level = risk.level if LEVEL_RANK[risk.level] >= 1 else "low"
            risk = Risk(level=level, category="medication", evidence=risk.evidence or text[:200])  # type: ignore[arg-type]
            outcome.risk = risk
            outcome.override_text = medication_reply()
            outcome.suggested_action = "notify_clinician"

        if risk.level == "none":
            return outcome

        flag, created = await upsert_flag(db, patient, session, risk, detector)
        outcome.flag_id, outcome.flag_created = flag.id, created

        if risk.level in ("medium", "high"):
            if created:
                await notifications_service.notify(
                    db,
                    patient,
                    flag,
                    risk.category,
                    risk.level,
                    risk.evidence,
                    settings=self.settings,
                )
            if risk.level == "high":
                script = safe_script(
                    risk.category,
                    await caregiver_first_name(db, patient),
                    self.settings.emergency_number,
                )
                if script:
                    outcome.override_text = script
                outcome.suggested_action = (
                    "notify_clinician" if risk.category == "abuse" else "notify_caregiver"
                )
            elif outcome.suggested_action is None:
                outcome.suggested_action = "notify_caregiver"
        return outcome
