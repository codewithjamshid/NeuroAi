"""One companion turn (TZ §4.8): audio→STT ∥ voice-emotion → fusion → LLM (companion.md,
CompanionReply) → SafetyService → TTS → persist messages / state / voice_metrics."""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.audio import AudioConversionError, synthesize_cached, wav_duration_s, webm_to_wav16k
from app.ai.chains import Chains, get_chains
from app.ai.prompts.loader import render
from app.ai.providers.base import ProviderUnavailable
from app.core.config import Settings
from app.core.errors import AppError
from app.modules.companion.schemas import (
    AiMessageOut,
    Candidate,
    CompanionReply,
    MessageResponse,
    PatientMessageOut,
)
from app.modules.patients import service as patients_service
from app.modules.patients.models import Patient
from app.modules.protocols import service as protocols_service
from app.modules.safety.keywords_uz import detect
from app.modules.safety.service import SafetyService
from app.modules.sessions import service as sessions_service
from app.modules.sessions.models import Message, Session, VoiceMetric
from app.modules.state.fusion import FusionInputs, fuse
from app.seeds import load_seed

log = logging.getLogger("neuroai.companion")

LOCAL_TZ = ZoneInfo("Asia/Samarkand")
LLM_TIMEOUT_S = 20.0
HISTORY_N = 12
MIN_EMOTION_S = 1.5
UNCLEAR = "[tushunarsiz nutq]"
ROLE_TO_LLM = {"patient": "user", "caregiver": "user", "system": "user", "ai": "assistant"}
ROLE_PREFIX = {"caregiver": "[parvarishchi] ", "system": "[tizim] "}


class LLMUnavailableError(AppError):
    status_code = 503
    code = "llm_unavailable"


class STTUnavailableError(AppError):
    status_code = 503
    code = "stt_unavailable"


class AudioInvalidError(AppError):
    status_code = 400
    code = "audio_invalid"


class PictogramUnknownError(AppError):
    status_code = 400
    code = "pictogram_unknown"


class EmptyInputError(AppError):
    status_code = 400
    code = "empty_input"


class FaceBatchInvalidError(AppError):
    status_code = 400
    code = "face_batch_invalid"


@dataclass
class TurnInput:
    audio: bytes | None = None
    text: str | None = None
    pictogram_key: str | None = None
    face_batch: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: int | None = None
    modality: str | None = None  # override (confirm → "pictogram")


def parse_face_batch(raw: str | None) -> list[dict[str, Any]]:
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise FaceBatchInvalidError("face_batch JSON emas") from exc
    if isinstance(data, dict):
        data = data.get("items") or data.get("batch") or [data]
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise FaceBatchInvalidError("face_batch ro'yxat bo'lishi kerak")
    return data


def needs_items() -> dict[str, dict[str, Any]]:
    try:
        return {item["key"]: item for item in load_seed("needs_uz")["items"]}
    except (FileNotFoundError, KeyError, TypeError):
        return {}


def candidate_label(key: str) -> tuple[str, str | None]:
    item = needs_items().get(key)
    if item is None:
        return key, None
    return item["label"], item.get("emoji")


def _fill_candidates(cands: list[Candidate]) -> list[Candidate]:
    items = needs_items()
    out: list[Candidate] = []
    for c in cands[:3]:
        item = items.get(c.key)
        if item is not None:
            out.append(
                c.model_copy(
                    update={
                        "label": c.label or item["label"],
                        "emoji": c.emoji or item.get("emoji"),
                    }
                )
            )
        else:
            out.append(c)
    return out


def patient_profile(patient: Patient) -> dict[str, Any]:
    return {
        "full_name": patient.full_name,
        "birth_year": patient.birth_year,
        "sex": patient.sex,
        "affected_side": patient.affected_side,
        "aphasia_type": patient.aphasia_type,
        "dysarthria": patient.dysarthria,
        "dialect": patient.dialect,
        "interests": patient.interests or [],
        "family_members": patient.family_members or [],
        "habits": patient.habits or [],
    }


def build_initial_prompt(patient: Patient, recent: list[Message]) -> str:
    words: list[str] = list(patient.interests or [])
    for member in patient.family_members or []:
        if isinstance(member, dict) and member.get("name"):
            words.append(str(member["name"]))
    seen: set[str] = set()
    for m in reversed([m for m in recent if m.role == "patient"][-3:]):
        for tok in (m.text or "").split():
            tok = tok.strip(".,!?").lower()
            if len(tok) > 3 and tok not in seen:
                seen.add(tok)
                words.append(tok)
    return ", ".join(dict.fromkeys(words))[:300]


async def recent_summaries(
    db: AsyncSession, patient_id: uuid.UUID, exclude: uuid.UUID
) -> list[str]:
    since = datetime.now(UTC) - timedelta(days=7)
    stmt = (
        select(Session.summary)
        .where(
            Session.patient_id == patient_id,
            Session.id != exclude,
            Session.started_at >= since,
            Session.summary.is_not(None),
        )
        .order_by(Session.started_at.desc())
        .limit(7)
    )
    out: list[str] = []
    for summary in (await db.scalars(stmt)).all():
        if isinstance(summary, dict) and summary.get("clinician_text"):
            out.append(str(summary["clinician_text"]))
    return out


async def today_plan(db: AsyncSession, patient: Patient) -> list[dict[str, Any]]:
    try:
        today = await protocols_service.build_today(db, patient)
    except Exception:
        log.exception("today plan failed")
        return []
    return [
        {"kind": i.kind, "title": i.title, "time": i.time, "done": i.done} for i in today.items[:12]
    ]


def history_messages(recent: list[Message]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in recent:
        role = ROLE_TO_LLM.get(m.role, "user")
        text = (m.text or "").strip()
        if not text:
            continue
        out.append({"role": role, "content": ROLE_PREFIX.get(m.role, "") + text})
    return out


async def _emotion(chains: Chains, wav: bytes) -> dict[str, Any] | None:
    if wav_duration_s(wav) < MIN_EMOTION_S:
        return None
    try:
        result = await chains.voice_emotion.call("analyze", wav)
    except ProviderUnavailable:
        return None
    except Exception:
        log.exception("voice emotion failed")
        return None
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    return {k: data.get(k) for k in ("label", "arousal", "valence", "dominance", "provider")}


def _voice_for_fusion(voice: dict[str, Any] | None) -> dict[str, Any] | None:
    if not voice:
        return None
    values = [voice.get("arousal"), voice.get("valence"), voice.get("dominance")]
    if voice.get("label") == "neutral" and all(not v for v in values):
        return None  # mock / no signal
    return voice


async def _resolve_input(
    chains: Chains, patient: Patient, recent: list[Message], turn: TurnInput
) -> tuple[str, str, bytes | None, float | None, str | None, dict[str, Any] | None, int]:
    """→ (text, modality, wav, stt_conf, stt_provider, voice, stt_ms)."""
    if turn.audio:
        try:
            wav = await webm_to_wav16k(turn.audio)
        except AudioConversionError as exc:
            raise AudioInvalidError(f"Audio o'qib bo'lmadi: {exc}") from exc
        started = time.perf_counter()
        stt_res, voice = await asyncio.gather(
            chains.stt.call(
                "transcribe", wav, lang="uz", initial_prompt=build_initial_prompt(patient, recent)
            ),
            _emotion(chains, wav),
            return_exceptions=True,
        )
        stt_ms = int((time.perf_counter() - started) * 1000)
        if isinstance(stt_res, BaseException):
            if isinstance(stt_res, ProviderUnavailable):
                raise STTUnavailableError("Eshitolmadim, matn bilan yozing") from stt_res
            raise stt_res
        if isinstance(voice, BaseException):
            voice = None
        return (
            (stt_res.text or "").strip(),
            turn.modality or "voice",
            wav,
            float(stt_res.confidence),
            stt_res.provider,
            voice,
            stt_ms,
        )
    if turn.pictogram_key:
        item = needs_items().get(turn.pictogram_key.strip())
        if item is None:
            raise PictogramUnknownError("Bunday piktogramma yo'q")
        return item["label"], turn.modality or "pictogram", None, None, None, None, 0
    text = (turn.text or "").strip()
    if not text:
        raise EmptyInputError("audio, text yoki pictogram_key yuboring")
    return text, turn.modality or "text", None, None, None, None, 0


def _save_wav(settings: Settings, session_id: uuid.UUID, message_id: uuid.UUID, wav: bytes) -> str:
    rel = f"audio/{session_id}/{message_id}.wav"
    path = settings.media_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(wav)
    return rel


async def handle_turn(
    db: AsyncSession,
    settings: Settings,
    session: Session,
    patient: Patient,
    turn: TurnInput,
    *,
    chains: Chains | None = None,
) -> MessageResponse:
    chains = chains or get_chains(settings)
    t0 = time.perf_counter()
    recent = await sessions_service.get_recent_messages(db, session.id, HISTORY_N)
    text, modality, wav, stt_conf, stt_provider, voice, stt_ms = await _resolve_input(
        chains, patient, recent, turn
    )

    # (c) fusion → patient_states
    hits = detect(text)
    mood_self = await patients_service.today_mood_self(db, patient.id)
    elapsed_min = None
    if session.started_at is not None:
        started = (
            session.started_at
            if session.started_at.tzinfo
            else session.started_at.replace(tzinfo=UTC)
        )
        elapsed_min = max(0.0, (datetime.now(UTC) - started).total_seconds() / 60)
    state_in = fuse(
        FusionInputs(
            text=text,
            face_batch=turn.face_batch,
            voice=_voice_for_fusion(voice),
            stt_confidence=stt_conf,
            mood_self=mood_self,
            latency_ms=turn.latency_ms,
            elapsed_min=elapsed_min,
            keyword_distress=any(h.level == "high" for h in hits),
        )
    )
    state = await sessions_service.store_state(db, session.id, state_in)

    # (g1) patient message (+ wav on disk, voice_metrics)
    patient_msg = await sessions_service.create_message(
        db,
        session.id,
        "patient",
        modality,
        text,
        commit=False,
        stt_confidence=stt_conf,
        stt_provider=stt_provider,
    )
    if wav is not None:
        try:
            patient_msg.audio_path = _save_wav(settings, session.id, patient_msg.id, wav)
        except OSError:
            log.exception("audio save failed")
    if voice:
        db.add(
            VoiceMetric(
                message_id=patient_msg.id,
                arousal=voice.get("arousal"),
                valence=voice.get("valence"),
                dominance=voice.get("dominance"),
                label=voice.get("label"),
                provider=voice.get("provider"),
            )
        )
    await db.commit()

    # (d) LLM
    system = render(
        "companion",
        patient_profile=json.dumps(patient_profile(patient), ensure_ascii=False),
        state_json=json.dumps(state_in.model_dump(exclude={"inputs"}), ensure_ascii=False),
        today_plan=json.dumps(await today_plan(db, patient), ensure_ascii=False),
        recent_summaries=json.dumps(
            await recent_summaries(db, patient.id, session.id), ensure_ascii=False
        ),
        now=datetime.now(LOCAL_TZ).isoformat(timespec="minutes"),
    )
    messages = history_messages(recent) + [{"role": "user", "content": text or UNCLEAR}]
    llm_started = time.perf_counter()
    try:
        reply: CompanionReply = await chains.llm.call(
            "generate",
            system=system,
            messages=messages,
            schema=CompanionReply,
            temperature=settings.llm_temperature,
            timeout_s=LLM_TIMEOUT_S,
            tier="fast",
        )
    except ProviderUnavailable as exc:
        raise LLMUnavailableError("Eshitolmadim, matn bilan yozing") from exc
    llm_ms = int((time.perf_counter() - llm_started) * 1000)
    llm_provider = _last_provider(chains.llm)

    # (e) safety
    safety = await SafetyService(settings).evaluate(
        db, patient=patient, session=session, text=text, llm_risk=reply.risk, intent=reply.intent
    )
    reply_text, tts_text = reply.reply_text.strip(), (reply.tts_text or reply.reply_text).strip()
    if safety.override_text:
        reply_text = tts_text = safety.override_text
    suggested_action = safety.suggested_action or reply.suggested_action
    needs_confirmation = reply.needs_confirmation and safety.risk.level != "high"
    candidates = _fill_candidates(reply.candidates) if needs_confirmation else []
    if needs_confirmation and not candidates:
        needs_confirmation = False

    # (f) TTS
    tts_started = time.perf_counter()
    tts_url, tts_provider = await synthesize_cached(chains, tts_text, settings.tts_speed)
    tts_ms = int((time.perf_counter() - tts_started) * 1000)

    # (g2) ai message
    llm_meta = {
        "provider": llm_provider,
        "latency_ms": llm_ms,
        "stt_ms": stt_ms,
        "tts_ms": tts_ms,
        "total_ms": int((time.perf_counter() - t0) * 1000),
        "risk": safety.risk.model_dump(),
        "detector": safety.detector,
        "flag_id": str(safety.flag_id) if safety.flag_id else None,
        "intent": reply.intent,
        "mood_estimate": reply.mood_estimate,
        "needs_confirmation": needs_confirmation,
        "candidates": [c.model_dump() for c in candidates],
        "suggested_action": suggested_action,
        "tts_text": tts_text,
        "tts_provider": tts_provider,
        "safe_script": bool(safety.override_text),
    }
    await sessions_service.create_message(
        db, session.id, "ai", "text", reply_text, llm_meta=llm_meta
    )

    return MessageResponse(
        patient_message=PatientMessageOut(
            text=text, stt_confidence=stt_conf, provider=stt_provider
        ),
        ai_message=AiMessageOut(text=reply_text, tts_url=tts_url, tts_provider=tts_provider),
        needs_confirmation=needs_confirmation,
        candidates=candidates,
        state=state,
        risk=safety.risk,
        suggested_action=suggested_action,
        meta={k: llm_meta[k] for k in ("provider", "latency_ms", "stt_ms", "tts_ms", "total_ms")},
    )


def _last_provider(chain: Any) -> str | None:
    for entry in chain.status():
        if entry.get("last_ok"):
            return str(entry["name"])
    return None


async def _label_for(db: AsyncSession, session: Session, key: str) -> str:
    label, _ = candidate_label(key)
    if label != key:
        return label
    for m in reversed(await sessions_service.get_recent_messages(db, session.id, 6)):
        if m.role == "ai" and m.llm_meta:
            for c in m.llm_meta.get("candidates") or []:
                if c.get("key") == key and c.get("label"):
                    return str(c["label"])
    return key


async def confirm(
    db: AsyncSession,
    settings: Settings,
    session: Session,
    patient: Patient,
    candidate_key: str,
    *,
    chains: Chains | None = None,
) -> MessageResponse:
    label = await _label_for(db, session, candidate_key.strip())
    await sessions_service.create_message(
        db,
        session.id,
        "system",
        "text",
        f"tasdiqlandi: {label}",
        llm_meta={"candidate_key": candidate_key},
    )
    return await handle_turn(
        db, settings, session, patient, TurnInput(text=label, modality="pictogram"), chains=chains
    )
