"""Exercise engine (M2): next item from the session plan, submit (CER → LLM judge → cue ladder →
adaptive level), skip, face summary scoring (§7.3)."""

import json
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.audio import synthesize_cached
from app.ai.chains import get_chains
from app.ai.prompts.loader import render
from app.ai.providers.base import ProviderUnavailable
from app.core.config import Settings
from app.core.errors import AppError
from app.modules.exercises import plan as planner
from app.modules.exercises.schemas import (
    CoachVerdict,
    ExerciseTemplateOut,
    FaceSummary,
    NextCue,
    NextCueOut,
    NextOut,
    Progress,
    SubmitOut,
    TemplateOut,
)
from app.modules.exercises.scoring import (
    ScoreResult,
    adaptive_level,
    next_cue,
    score_answer,
    session_metrics,
)
from app.modules.interpreter.service import patient_profile, to_wav, transcribe
from app.modules.patients.models import Patient, PatientLevel
from app.modules.sessions import service as sessions_service
from app.modules.sessions.models import ExerciseAttempt, ExerciseTemplate, Session
from app.modules.users.errors import ConflictError, NotFoundError
from app.modules.users.models import User

log = logging.getLogger(__name__)

MAX_UNCLEAR = 2
FATIGUE_BREAK = 0.7
FACE_CORRECT = 0.7
FACE_PARTIAL = 0.4
TEXT_CONFIDENCE = 1.0
DISTRACTORS = 4
COACH_TIMEOUT_S = 10.0  # Gemini 504s seen at ~14 s; fail over to OpenAI sooner
COACH_TEMPERATURE = 0.2

UNCLEAR_TEXT = "Eshitolmadim, yana bir bor aytasizmi?"
SKIPPED_TEXT = "Bu safar o'tkazamiz. Keyingisiga o'tamiz."
EXHAUSTED_TEXT = "Bo'ldi, keyingi safar chiqadi. Keyingisiga o'tamiz."
BREAK_TEXT = "Yaxshi ishladingiz. Keling, biroz dam olamiz."


def _answers(template: ExerciseTemplate) -> list[str]:
    return [str(a) for a in (template.expected or {}).get("answers") or [] if str(a).strip()]


def _fatigue(session: Session) -> float:
    try:
        return float((session.state_snapshot or {}).get("fatigue") or 0.0)
    except (TypeError, ValueError):
        return 0.0


async def _tts(settings: Settings, text: str | None) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    return await synthesize_cached(get_chains(settings), text, settings.tts_speed)


# --- next -----------------------------------------------------------------------------------


async def _template_by_key(db: AsyncSession, key: str) -> ExerciseTemplate | None:
    return await db.scalar(select(ExerciseTemplate).where(ExerciseTemplate.key == key))


async def _session_attempts(db: AsyncSession, session_id: uuid.UUID) -> list[ExerciseAttempt]:
    stmt = (
        select(ExerciseAttempt)
        .where(ExerciseAttempt.session_id == session_id)
        .order_by(ExerciseAttempt.created_at, ExerciseAttempt.id)
    )
    return list((await db.scalars(stmt)).all())


async def _finish(db: AsyncSession, session: Session, plan: dict[str, Any]) -> dict[str, Any]:
    attempts = await _session_attempts(db, session.id)
    metrics = session_metrics(
        [
            {
                "score": a.score or 0.0,
                "result": a.result,
                "cue_level": a.cue_level,
                "response_ms": a.response_ms,
            }
            for a in attempts
        ]
    )
    planner.save_plan(session, plan)
    session.state_snapshot = {**(session.state_snapshot or {}), "exercise_summary": metrics}
    await db.commit()
    return metrics


async def _attempt_out(
    settings: Settings, template: ExerciseTemplate, attempt: ExerciseAttempt, plan: dict[str, Any]
) -> NextOut:
    url, _ = await _tts(settings, template.prompt_text)
    return NextOut(
        attempt_id=attempt.id,
        template=TemplateOut(
            id=template.id,
            key=template.key,
            category=template.category,
            subtype=template.subtype,
            level=template.level,
            prompt_text=template.prompt_text,
            prompt_tts_url=url,
            stimulus=template.stimulus,
            cues=template.cues,
        ),
        cue_level=attempt.cue_level,
        progress=Progress(index=int(plan["index"]) + 1, total=len(plan["keys"])),
    )


async def next_item(
    db: AsyncSession, settings: Settings, session: Session, patient: Patient
) -> NextOut:
    plan = planner.get_plan(session)
    if not plan:
        plan = await planner.build_plan(db, patient)
        planner.save_plan(session, plan)
        await db.commit()
    if plan.get("attempt_id"):  # page reload: same pending attempt again
        attempt = await db.get(ExerciseAttempt, uuid.UUID(plan["attempt_id"]))
        template = await db.get(ExerciseTemplate, attempt.template_id) if attempt else None
        if attempt is not None and template is not None:
            return await _attempt_out(settings, template, attempt, plan)
    keys: list[str] = plan["keys"]
    while int(plan["index"]) < len(keys):
        template = await _template_by_key(db, keys[int(plan["index"])])
        if template is not None:
            break
        plan["index"] = int(plan["index"]) + 1  # key vanished from the table: skip it
    else:
        summary = await _finish(db, session, plan)
        return NextOut(done=True, summary=summary)
    answers = _answers(template)
    attempt = ExerciseAttempt(
        session_id=session.id,
        template_id=template.id,
        category=template.category,
        expected_answer=answers[0] if answers else None,
        cue_level=0,
        llm_judgement={"unclear": 0, "history": []},
    )
    db.add(attempt)
    await db.flush()
    plan["attempt_id"] = str(attempt.id)
    planner.save_plan(session, plan)
    await db.commit()
    return await _attempt_out(settings, template, attempt, plan)


# --- submit ---------------------------------------------------------------------------------


async def _stt_prompt(db: AsyncSession, template: ExerciseTemplate, plan: dict[str, Any]) -> str:
    """Expected answer + 4 distractors from the other plan items (TZ §7.2)."""
    words = [a for a in _answers(template)[:1]]
    others = [k for k in plan.get("keys", []) if k != template.key]
    if others:
        stmt = select(ExerciseTemplate.expected).where(ExerciseTemplate.key.in_(others))
        for expected in (await db.scalars(stmt)).all():
            first = ((expected or {}).get("answers") or [None])[0]
            if first and first not in words:
                words.append(str(first))
            if len(words) >= 1 + DISTRACTORS:
                break
    return ", ".join(words)


async def _coach(
    settings: Settings,
    template: ExerciseTemplate,
    patient: Patient,
    session: Session,
    recognized: str,
    conf: float,
    scored: ScoreResult,
    cue_level: int,
) -> CoachVerdict | None:
    exercise = {
        "subtype": template.subtype,
        "prompt_text": template.prompt_text,
        "expected": template.expected,
        "cues": template.cues,
    }
    state = {
        k: v
        for k, v in (session.state_snapshot or {}).items()
        if k not in ("exercise_plan", "exercise_summary")
    }
    system = render(
        "coach",
        exercise_json=json.dumps(exercise, ensure_ascii=False),
        recognized=recognized,
        stt_confidence=f"{conf:.2f}",
        cer_score=f"{scored.score:.2f}",
        cue_level=cue_level,
        patient_profile=json.dumps(patient_profile(patient), ensure_ascii=False),
        state_json=json.dumps(state, ensure_ascii=False, default=str),
    )
    try:
        return await get_chains(settings).llm.call(
            "generate",
            system=system,
            messages=[{"role": "user", "content": recognized or "(javob yo'q)"}],
            schema=CoachVerdict,
            temperature=COACH_TEMPERATURE,
            timeout_s=COACH_TIMEOUT_S,
            tier="fast",
        )
    except ProviderUnavailable:
        log.warning("coach: llm unavailable, deterministic feedback")
        return None


def decide(
    scored: ScoreResult,
    verdict: CoachVerdict | None,
    cue_level: int,
    cues: dict[str, Any] | None,
    answer: str,
    fatigue: float = 0.0,
) -> tuple[str, str, str, NextCue | None]:
    """→ (result, feedback_text, next_action, next_cue). Verdict wins when present (§7.2)."""
    cue = next_cue(cue_level, cues, answer)
    if verdict is not None:
        result, feedback = verdict.result, verdict.feedback_text.strip() or verdict.tts_text
        if result == "correct" or verdict.next_action == "suggest_break" or cue is None:
            action = "suggest_break" if verdict.next_action == "suggest_break" else "next_item"
            return result, feedback or EXHAUSTED_TEXT, action, None
        if verdict.next_cue is not None and verdict.next_cue.text.strip():
            cue = (cue[0], verdict.next_cue.text.strip())
        return result, feedback, "retry_with_cue", NextCue(level=cue[0], text=cue[1])
    result = scored.result
    if result == "correct":
        return result, f"To'g'ri! {answer.capitalize()}.", "next_item", None
    if cue is None:
        return result, EXHAUSTED_TEXT, "next_item", None
    if result == "partial":
        feedback = (
            "Deyarli! Birinchi bo'g'in to'g'ri."
            if scored.first_syllable_ok
            else "Deyarli! Yana bir bor urinib ko'ramiz."
        )
    else:
        feedback = "Hozircha emas. Keling, ishora beraman."
    action = "retry_with_cue"
    if fatigue >= FATIGUE_BREAK:
        return result, BREAK_TEXT, "suggest_break", None
    return result, feedback, action, NextCue(level=cue[0], text=cue[1])


async def _set_level(db: AsyncSession, patient_id: uuid.UUID, category: str, level: int) -> None:
    stmt = select(PatientLevel).where(
        PatientLevel.patient_id == patient_id, PatientLevel.category == category
    )
    row = await db.scalar(stmt)
    if row is None:
        db.add(PatientLevel(patient_id=patient_id, category=category, level=level))
    elif not row.locked_by_clinician:
        row.level = level


async def _finalize(
    db: AsyncSession, session: Session, plan: dict[str, Any], patient: Patient
) -> None:
    """Item done: advance the plan and apply the adaptive level rule (§7.5)."""
    plan["index"] = int(plan.get("index", 0)) + 1
    plan["attempt_id"] = None
    attempts = await _session_attempts(db, session.id)
    history = [(a.result, a.cue_level) for a in attempts if a.result]
    start = int(plan.get("streak_from", 0))
    level = int(plan.get("level", 1))
    new_level = adaptive_level(history[start:], level)  # type: ignore[arg-type]
    if new_level != level:
        plan["level"], plan["streak_from"] = new_level, len(history)
        await _set_level(db, patient.id, plan.get("category", "speech"), new_level)
    planner.save_plan(session, plan)


async def _load_attempt(
    db: AsyncSession, user: User, attempt_id: uuid.UUID
) -> tuple[ExerciseAttempt, Session, Patient, dict[str, Any]]:
    attempt = await db.get(ExerciseAttempt, attempt_id)
    if attempt is None:
        raise NotFoundError("Urinish topilmadi")
    session = await sessions_service.get_session_for_user(db, attempt.session_id, user)
    patient = await db.get(Patient, session.patient_id)
    if patient is None:
        raise NotFoundError("Bemor topilmadi")
    plan = planner.get_plan(session) or {}
    if plan and plan.get("attempt_id") != str(attempt.id):
        raise ConflictError("Bu urinish allaqachon yakunlangan")
    return attempt, session, patient, plan


def face_score(summary: FaceSummary) -> tuple[float, str]:
    score = (
        0.5 * min(summary.reps / summary.target_reps, 1.0)
        + 0.3 * summary.mean_amplitude
        + 0.2 * summary.fsi
    )
    score = round(score, 3)
    result = (
        "correct" if score >= FACE_CORRECT else "partial" if score >= FACE_PARTIAL else "incorrect"
    )
    return score, result


def face_feedback(summary: FaceSummary, result: str) -> str:
    if result == "correct":
        text = f"Yaxshi! {summary.reps} ta takror bajarildi."
    elif summary.reps < summary.target_reps:
        text = f"Yaxshi urinish. Yana {summary.target_reps - summary.reps} ta takror qiling."
    else:
        text = "Harakatni kengroq va sekinroq bajarib ko'ring."
    if summary.fsi < 0.6:
        text += " Ikkala tomonni teng ko'tarishga harakat qiling."
    return text


async def submit(
    db: AsyncSession,
    settings: Settings,
    user: User,
    attempt_id: uuid.UUID,
    *,
    audio: bytes | None = None,
    text: str | None = None,
    face_summary: FaceSummary | None = None,
    response_ms: int | None = None,
) -> SubmitOut:
    attempt, session, patient, plan = await _load_attempt(db, user, attempt_id)
    if response_ms is not None:
        attempt.response_ms = response_ms
    if face_summary is not None:
        score, result = face_score(face_summary)
        feedback = face_feedback(face_summary, result)
        attempt.category, attempt.score, attempt.result = "face", score, result
        attempt.llm_judgement = {
            **(attempt.llm_judgement or {}),
            "face_summary": face_summary.model_dump(),
        }
        if plan:
            await _finalize(db, session, plan, patient)
        await db.commit()
        url, provider = await _tts(settings, feedback)
        return SubmitOut(
            score=score, result=result, feedback_text=feedback, tts_url=url,
            tts_provider=provider, next_action="next_item",
        )  # fmt: skip

    template = await db.get(ExerciseTemplate, attempt.template_id) if attempt.template_id else None
    if template is None:
        raise NotFoundError("Mashq shabloni topilmadi")
    answers = _answers(template)
    text = (text or "").strip() if text is not None else None
    if text is not None:
        recognized, conf = text, TEXT_CONFIDENCE
    elif audio:
        wav = await to_wav(audio)
        recognized, conf, _ = await transcribe(
            get_chains(settings), wav, await _stt_prompt(db, template, plan)
        )
    else:
        raise AppError(
            "audio, text yoki face_summary kerak", code="input_required", status_code=400
        )

    scored = score_answer(answers, recognized, conf)
    judgement = dict(attempt.llm_judgement or {})
    history = list(judgement.get("history") or [])
    attempt.recognized_text = recognized
    if scored.result == "unclear":
        unclear = int(judgement.get("unclear") or 0) + 1
        judgement["unclear"] = unclear
        if unclear >= MAX_UNCLEAR:
            attempt.result, attempt.score = "skipped", 0.0
            result, feedback, action = "skipped", SKIPPED_TEXT, "next_item"
            if plan:
                await _finalize(db, session, plan, patient)
        else:
            result, feedback, action = "unclear", UNCLEAR_TEXT, "retry_with_cue"
        attempt.llm_judgement = judgement
        await db.commit()
        url, provider = await _tts(settings, feedback)
        return SubmitOut(
            score=0.0, result=result, recognized_text=recognized, feedback_text=feedback,
            tts_url=url, tts_provider=provider, next_action=action,
        )  # fmt: skip

    verdict = None
    if scored.needs_llm_judge:
        verdict = await _coach(
            settings, template, patient, session, recognized, conf, scored, attempt.cue_level
        )
    answer = scored.best_expected or (answers[0] if answers else "")
    result, feedback, action, cue = decide(
        scored, verdict, attempt.cue_level, template.cues, answer, _fatigue(session)
    )
    history.append(
        {
            "cue_level": attempt.cue_level,
            "recognized": recognized,
            "stt_confidence": conf,
            "score": scored.score,
            "result": result,
            "judge": "llm" if verdict else "cer",
            "reason": scored.reason,
        }
    )
    judgement.update(history=history, verdict=verdict.model_dump() if verdict else None)
    attempt.expected_answer = answer or attempt.expected_answer
    attempt.score, attempt.result, attempt.llm_judgement = scored.score, result, judgement
    if action == "retry_with_cue" and cue is not None:
        attempt.cue_level = cue.level
    elif plan:
        await _finalize(db, session, plan, patient)
    await db.commit()

    url, provider = await _tts(settings, feedback)
    cue_out = None
    if cue is not None:
        cue_url, _ = await _tts(settings, cue.text)
        cue_out = NextCueOut(level=cue.level, text=cue.text, tts_url=cue_url)
    return SubmitOut(
        score=scored.score,
        result=result,
        recognized_text=recognized,
        feedback_text=feedback,
        tts_url=url,
        tts_provider=provider,
        next_action=action,  # type: ignore[arg-type]
        next_cue=cue_out,
    )


async def skip(db: AsyncSession, user: User, attempt_id: uuid.UUID) -> None:
    attempt, session, patient, plan = await _load_attempt(db, user, attempt_id)
    attempt.result, attempt.score = "skipped", 0.0
    if plan:
        await _finalize(db, session, plan, patient)
    await db.commit()


async def list_templates(
    db: AsyncSession, category: str | None, level: int | None, limit: int, offset: int
) -> list[ExerciseTemplateOut]:
    stmt = select(ExerciseTemplate).where(ExerciseTemplate.active.is_(True))
    if category:
        stmt = stmt.where(ExerciseTemplate.category == category)
    if level is not None:
        stmt = stmt.where(ExerciseTemplate.level == level)
    stmt = stmt.order_by(ExerciseTemplate.category, ExerciseTemplate.level, ExerciseTemplate.key)
    rows = (await db.scalars(stmt.limit(limit).offset(offset))).all()
    return [ExerciseTemplateOut.model_validate(r) for r in rows]
