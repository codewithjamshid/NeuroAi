"""Interpreter (M3, TZ §7.7): STT → LLM 3 candidates (alias fallback) → confirm → TTS + note."""

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from rapidfuzz.distance import Levenshtein
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.audio import AudioConversionError, synthesize_cached, webm_to_wav16k
from app.ai.chains import get_chains
from app.ai.prompts.loader import render
from app.ai.providers.base import ProviderUnavailable
from app.core.config import Settings
from app.core.errors import AppError
from app.core.uz_text import normalize
from app.modules.interpreter.schemas import (
    BoardItem,
    BoardOut,
    BodyPart,
    Candidate,
    ConfirmIn,
    ConfirmOut,
    GuessOut,
    InterpreterGuess,
)
from app.modules.patients import service as patients_service
from app.modules.patients.models import Patient
from app.modules.sessions import service as sessions_service
from app.modules.sessions.models import Interpretation, Session
from app.modules.users.errors import NotFoundError
from app.modules.users.models import User
from app.seeds import load_seed

log = logging.getLogger(__name__)

LOW_CONF = 0.3
TEXT_CONFIDENCE = 1.0
DEFAULT_KEYS = ["water", "food", "toilet"]
FALLBACK_P = [0.5, 0.3, 0.2]
STT_PROMPT_LABELS = 12
LLM_TIMEOUT_S = 12.0
LLM_TEMPERATURE = 0.3

BODY_SPOKEN = {
    "head": "Boshim og'riyapti.",
    "chest": "Ko'kragim og'riyapti.",
    "belly": "Qornim og'riyapti.",
    "arm": "Qo'lim og'riyapti.",
    "leg": "Oyog'im og'riyapti.",
    "back": "Orqam og'riyapti.",
}


# --- vocabulary ---------------------------------------------------------------------------------


def needs_items() -> list[dict[str, Any]]:
    return list(load_seed("needs_uz")["items"])


def body_map() -> list[dict[str, Any]]:
    return list(load_seed("needs_uz").get("body_map") or [])


def person_key(name: str) -> str:
    return "person:" + normalize(name).replace(" ", "_")


def person_items(patient: Patient) -> list[dict[str, Any]]:
    template = load_seed("needs_uz").get("person_template") or {}
    out: list[dict[str, Any]] = []
    for member in patient.family_members or []:
        name = str(member.get("name") or "").strip()
        if not name:
            continue
        out.append(
            {
                "key": person_key(name),
                "label": name,
                "emoji": template.get("emoji", "👤"),
                "group": template.get("group", "oila"),
                "spoken": str(template.get("spoken", "{name}ni chaqiring.")).replace(
                    "{name}", name
                ),
                "aliases": [name, str(member.get("relation") or "")],
            }
        )
    return out


def vocab_for(patient: Patient) -> dict[str, dict[str, Any]]:
    """key → item (needs_uz + person:* from the patient card), in board order."""
    return {i["key"]: i for i in [*needs_items(), *person_items(patient)]}


def patient_profile(patient: Patient) -> dict[str, Any]:
    return {
        "name": patient.full_name,
        "birth_year": patient.birth_year,
        "aphasia_type": patient.aphasia_type,
        "dysarthria": patient.dysarthria,
        "dialect": patient.dialect,
        "interests": patient.interests or [],
        "family": [m.get("name") for m in (patient.family_members or [])],
    }


# --- history --------------------------------------------------------------------------------


async def confirmed_counts(db: AsyncSession, patient_id: uuid.UUID) -> dict[str, int]:
    stmt = (
        select(Interpretation.chosen, func.count(Interpretation.id))
        .where(Interpretation.patient_id == patient_id, Interpretation.chosen.is_not(None))
        .group_by(Interpretation.chosen)
    )
    return {key: int(n) for key, n in (await db.execute(stmt)).all() if key}


async def recent_confirmed_keys(
    db: AsyncSession, patient_id: uuid.UUID, hours: int = 24
) -> list[str]:
    since = datetime.now(UTC) - timedelta(hours=hours)
    stmt = (
        select(Interpretation.chosen)
        .where(
            Interpretation.patient_id == patient_id,
            Interpretation.chosen.is_not(None),
            Interpretation.updated_at >= since,
        )
        .order_by(Interpretation.updated_at.desc())
        .limit(20)
    )
    return [k for k in (await db.scalars(stmt)).all() if k]


# --- candidates -----------------------------------------------------------------------------


def _cand(item: dict[str, Any], p: float) -> Candidate:
    return Candidate(key=item["key"], label=item["label"], emoji=item.get("emoji"), p=round(p, 3))


def frequent_candidates(
    vocab: dict[str, dict[str, Any]], counts: dict[str, int]
) -> list[Candidate]:
    """3 most frequently confirmed intents, padded with water/food/toilet."""
    keys = [k for k, _ in sorted(counts.items(), key=lambda kv: -kv[1]) if k in vocab]
    for key in DEFAULT_KEYS:
        if key not in keys and key in vocab:
            keys.append(key)
    return [_cand(vocab[k], FALLBACK_P[i]) for i, k in enumerate(keys[:3])]


def _alias_score(token: str, word: str) -> float:
    if token == word:
        return 1.0
    if len(token) >= 2 and word.startswith(token):
        return 0.6 + 0.3 * len(token) / len(word)
    sim = Levenshtein.normalized_similarity(token, word)
    if sim >= 0.6:
        return sim * 0.8
    if len(token) >= 2 and word[:2] == token[:2]:
        return 0.3
    return 0.0


def alias_candidates(
    vocab: dict[str, dict[str, Any]], raw: str, counts: dict[str, int]
) -> list[Candidate]:
    """No LLM: normalize() + alias/label prefix & fuzzy match, ranked by score then frequency."""
    tokens = [t for t in normalize(raw).split() if t]
    scored: list[tuple[float, int, int, str]] = []
    for order, (key, item) in enumerate(vocab.items()):
        words = {
            w
            for alias in [item.get("label", ""), *item.get("aliases", [])]
            for w in normalize(alias).split()
        }
        best = sum(max((_alias_score(t, w) for w in words), default=0.0) for t in tokens)
        if best > 0:
            scored.append((round(best, 4), counts.get(key, 0), -order, key))
    scored.sort(reverse=True)
    top = scored[:3]
    total = sum(s for s, *_ in top) or 1.0
    out = [_cand(vocab[key], 0.9 * score / total) for score, _, _, key in top]
    seen = {c.key for c in out}
    for cand in frequent_candidates(vocab, counts):
        if len(out) >= 3:
            break
        if cand.key not in seen:
            out.append(cand.model_copy(update={"p": 0.05}))
            seen.add(cand.key)
    return out


def repair_candidates(
    cands: list[Candidate], vocab: dict[str, dict[str, Any]], counts: dict[str, int]
) -> list[Candidate]:
    """Exactly 3; keys must exist in the vocab (unknown → 'other' keeping the LLM label)."""
    out: list[Candidate] = []
    seen: set[tuple[str, str]] = set()
    for cand in cands:
        key = (cand.key or "").strip()
        item = vocab.get(key)
        if item is not None:
            fixed = _cand(item, cand.p)
        else:
            fixed = Candidate(
                key="other", label=cand.label or "Boshqa", emoji=cand.emoji or "❓", p=cand.p
            )
        ident = (fixed.key, fixed.label.lower())
        if ident in seen:
            continue
        seen.add(ident)
        out.append(fixed)
        if len(out) == 3:
            break
    for cand in frequent_candidates(vocab, counts):
        if len(out) >= 3:
            break
        if (cand.key, cand.label.lower()) not in seen:
            out.append(cand.model_copy(update={"p": 0.05}))
            seen.add((cand.key, cand.label.lower()))
    return out[:3]


def _stt_prompt(vocab: dict[str, dict[str, Any]], counts: dict[str, int]) -> str:
    ordered = sorted(vocab.values(), key=lambda i: -counts.get(i["key"], 0))
    return ", ".join(i["label"] for i in ordered[:STT_PROMPT_LABELS])


# --- audio / providers ----------------------------------------------------------------------


async def to_wav(data: bytes) -> bytes:
    if data[:4] == b"RIFF":
        return data
    try:
        return await webm_to_wav16k(data)
    except AudioConversionError as exc:
        raise AppError("Audio o'qib bo'lmadi", code="audio_invalid", status_code=400) from exc


async def transcribe(chains: Any, wav: bytes, initial_prompt: str) -> tuple[str, float, str | None]:
    try:
        result = await chains.stt.call("transcribe", wav, lang="uz", initial_prompt=initial_prompt)
    except ProviderUnavailable:
        return "", 0.0, None
    return result.text.strip(), float(result.confidence), result.provider


async def _llm_guess(
    chains: Any,
    patient: Patient,
    raw: str,
    conf: float,
    recent: list[str],
    vocab: dict[str, dict[str, Any]],
) -> InterpreterGuess | None:
    system = render(
        "interpreter",
        patient_profile=json.dumps(patient_profile(patient), ensure_ascii=False),
        raw_transcript=raw,
        stt_confidence=f"{conf:.2f}",
        now=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
        recent_intents=json.dumps(recent, ensure_ascii=False),
        habits=json.dumps(patient.habits or [], ensure_ascii=False),
        needs_vocab=json.dumps({k: v["label"] for k, v in vocab.items()}, ensure_ascii=False),
    )
    try:
        return await chains.llm.call(
            "generate",
            system=system,
            messages=[{"role": "user", "content": raw}],
            schema=InterpreterGuess,
            temperature=LLM_TEMPERATURE,
            timeout_s=LLM_TIMEOUT_S,
            tier="fast",
        )
    except ProviderUnavailable:
        log.warning("interpreter: llm unavailable, alias fallback")
        return None


# --- use cases --------------------------------------------------------------------------------


async def guess(
    db: AsyncSession,
    settings: Settings,
    patient: Patient,
    user: User,
    *,
    audio: bytes | None,
    text: str | None,
    session_id: uuid.UUID | None,
) -> GuessOut:
    text = (text or "").strip()
    if not audio and not text:
        raise AppError("audio yoki text kerak", code="input_required", status_code=400)
    if session_id is not None:
        session = await sessions_service.get_session_for_user(db, session_id, user)
    else:
        session = await sessions_service.create_session(db, patient, user, "interpreter")
    chains = get_chains(settings)
    vocab = vocab_for(patient)
    counts = await confirmed_counts(db, patient.id)

    if text:
        raw, conf, provider, modality = text, TEXT_CONFIDENCE, None, "text"
    else:
        wav = await to_wav(audio or b"")
        raw, conf, provider = await transcribe(chains, wav, _stt_prompt(vocab, counts))
        modality = "voice"
    await sessions_service.create_message(
        db, session.id, "patient", modality, raw, commit=False,
        stt_confidence=conf, stt_provider=provider,
    )  # fmt: skip

    llm_guess: InterpreterGuess | None = None
    if not raw or conf < LOW_CONF:
        candidates, board = frequent_candidates(vocab, counts), True
    else:
        recent = await recent_confirmed_keys(db, patient.id)
        llm_guess = await _llm_guess(chains, patient, raw, conf, recent, vocab)
        if llm_guess is None:
            candidates, board = alias_candidates(vocab, raw, counts), False
        else:
            candidates = repair_candidates(llm_guess.candidates, vocab, counts)
            board = llm_guess.board_suggested
    stored = [c.model_dump() for c in candidates]
    if llm_guess is not None and stored:  # keep the LLM texts for the top candidate (confirm)
        stored[0].update(
            note=llm_guess.family_note.strip(),
            spoken=llm_guess.spoken_text.strip(),
            follow_up=llm_guess.follow_up,
        )
    row = Interpretation(
        session_id=session.id,
        patient_id=patient.id,
        raw_transcript=raw,
        stt_confidence=conf,
        candidates=stored,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return GuessOut(
        interpretation_id=row.id,
        session_id=session.id,
        raw_transcript=raw,
        confidence=conf,
        candidates=candidates,
        board_suggested=board,
    )


def family_note_template(label: str) -> str:
    return (
        f"Bemor {label} so'rayapti. Iltimos, yordam bering va "
        f'"{label}" so\'zini sekin takrorlang.'
    )


def resolve_choice(
    data: ConfirmIn, vocab: dict[str, dict[str, Any]], candidates: list[dict[str, Any]]
) -> tuple[str, str, str]:
    """→ (chosen key, label, spoken_text)."""
    key = (data.candidate_key or "").strip()
    custom = (data.custom_text or "").strip()
    if not key and not custom:
        raise AppError(
            "candidate_key yoki custom_text kerak", code="input_required", status_code=400
        )
    body_key = key.removeprefix("body:")
    if body_key in BODY_SPOKEN:
        part = next((b for b in body_map() if b["key"] == body_key), {"label": body_key})
        return f"body:{body_key}", part["label"], BODY_SPOKEN[body_key]
    item = vocab.get(key)
    if item is not None and not custom:
        return key, item["label"], item["spoken"]
    cand = next((c for c in candidates if c.get("key") == key), None) if key else None
    label = custom or (cand or {}).get("label") or "Boshqa"
    spoken = custom or (cand or {}).get("spoken") or label
    return "other", label, spoken


async def confirm(db: AsyncSession, settings: Settings, user: User, data: ConfirmIn) -> ConfirmOut:
    row = await db.get(Interpretation, data.interpretation_id)
    if row is None or row.patient_id is None:
        raise NotFoundError("Tarjima topilmadi")
    patient = await patients_service.get_patient_for_user(db, row.patient_id, user)
    candidates = list(row.candidates or [])
    chosen, label, spoken = resolve_choice(data, vocab_for(patient), candidates)
    top = candidates[0] if candidates else {}
    note = top.get("note") if top.get("key") == chosen and top.get("note") else None
    note = note or family_note_template(label)
    follow_up = "body_map" if chosen == "pain" else "none"
    tts_url, provider = await synthesize_cached(get_chains(settings), spoken, settings.tts_speed)
    row.chosen, row.spoken_text, row.family_note, row.confirmed_by = chosen, spoken, note, user.role
    if row.session_id is not None:
        await sessions_service.create_message(
            db, row.session_id, "ai", "text", spoken, commit=False,
            llm_meta={"kind": "interpreter", "chosen": chosen, "tts_url": tts_url},
        )  # fmt: skip
    await db.commit()
    return ConfirmOut(
        spoken_text=spoken,
        tts_url=tts_url,
        tts_provider=provider,
        family_note=note,
        follow_up=follow_up,
        chosen=chosen,
    )


async def board(db: AsyncSession, patient: Patient) -> BoardOut:
    counts = await confirmed_counts(db, patient.id)
    items = [*needs_items(), *person_items(patient)]
    ordered = sorted(enumerate(items), key=lambda pair: (-counts.get(pair[1]["key"], 0), pair[0]))
    return BoardOut(
        items=[
            BoardItem(key=i["key"], label=i["label"], emoji=i.get("emoji"), group=i.get("group"))
            for _, i in ordered
        ],
        body_map=[
            BodyPart(key=b["key"], label=b["label"], emoji=b.get("emoji")) for b in body_map()
        ],
    )


async def list_interpretations(
    db: AsyncSession, patient_id: uuid.UUID, limit: int, offset: int
) -> list[Interpretation]:
    stmt = (
        select(Interpretation)
        .where(Interpretation.patient_id == patient_id)
        .order_by(Interpretation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await db.scalars(stmt)).all())


async def session_for(db: AsyncSession, session_id: uuid.UUID) -> Session | None:
    return await db.get(Session, session_id)
