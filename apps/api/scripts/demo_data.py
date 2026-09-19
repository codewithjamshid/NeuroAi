"""demo_data — 14 kunlik "Bobur aka" tarixi + 2-bemor Gulnora (TZ §11.2, T-17).

`make demo` = seed + bu skript. Idempotent: marker = Bobur's Session(mode="checkin",
summary.demo_marker=true) → "already loaded". `--reset` faqat shu skript yaratgan qatorlarni
(summary/meta/payload ichida "demo": true, dori notes="demo") ikki demo bemor uchun o'chiradi va
qayta yuklaydi. Postgres va sqlite'da ishlaydi (bola qatorlar oldidan ota qator flush qilinadi).
"""

import argparse
import asyncio
import json
import random
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # `python scripts/demo_data.py`

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

import app.db.registry  # noqa: F401, E402
from app.ai.prompts.safe_scripts_uz import safe_script  # noqa: E402
from app.db.session import dispose_engine, get_sessionmaker  # noqa: E402
from app.modules.clinician import service as clinician_service  # noqa: E402
from app.modules.patients.models import MoodEntry, Patient, PatientLevel, RedFlag  # noqa: E402
from app.modules.protocols import service as protocols_service  # noqa: E402
from app.modules.protocols.models import Medication, MedicationLog  # noqa: E402
from app.modules.protocols.schemas import ProtocolCreate  # noqa: E402
from app.modules.sessions.models import (  # noqa: E402
    ExerciseAttempt,
    ExerciseTemplate,
    FaceMetric,
    Interpretation,
    Message,
    PatientState,
    Report,
    Session,
    VoiceMetric,
)
from app.modules.users.models import AuditLog, Notification, User  # noqa: E402
from scripts.seed import seed  # noqa: E402

DAYS = 14
FLAG_DAY = 4  # 5-kun (0-index)
DIP_DAYS = {3, 4}
COMPANION_DAYS = {0, 1, 3, 4, 6, 7, 9, 10, 12, 13}
INTERPRETER_DAYS = {2, 5, 8, 11, 13}
SKIP_FACE_DAYS = {1, 8, 12}  # oxirgi hafta: 3 ta kategoriya-kun o'tkazib yuborilgan → ~86 %
SKIP_COG_DAYS = {3, 10}
MED_MISSED = {(2, 1), (5, 0), (9, 1), (12, 0)}  # (kun, dori) → 24/28 = 86 %
FLAG_EVIDENCE = "hech narsaning foydasi yo'q"
FLAG_NOTE = (
    "Qizi Nilufar bilan gaplashdim, kayfiyat so'rovi kuchaytirildi, "
    "psixolog konsultatsiyasi tavsiya qilindi. — D. Karimova"
)
GULNORA = {
    "full_name": "Gulnora Yusupova",
    "birth_year": 1968,
    "sex": "female",
    "stroke_type": "ischemic",
    "affected_side": "right",
    "aphasia_type": None,
    "dysarthria": True,
    "facial_palsy_side": "right",
    "dominant_hand": "right",
    "dialect": "khorezm",
    "interests": ["kashtachilik", "nabiralar"],
    "family_members": [{"name": "Dilshod", "relation": "o'g'li"}],
    "habits": ["ertalab bog'da yuradi"],
    "notes": "Xiva. Demo bemor (dizartriya).",
}
GULNORA_TEMPLATE = "dysarthria_m1"
MEDS = [("Dori A", "1 tabletka", "09:00", 4), ("Dori B", "1 tabletka", "21:00", 16)]
WEEKDAYS_UZ = ["dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba", "yakshanba"]
WORDS_FALLBACK = ["suv", "choy", "non", "olma", "uy", "kitob", "qo'l", "ko'z"]
OFFSETS = [
    (0.12, -1.0),
    (0.06, -0.5),
    (0.0, 0.0),
    (-0.06, 0.5),
    (-0.12, 1.0),
    (0.09, -0.5),
    (-0.09, 0.5),
]

COMPANION_EARLY = [
    (
        "Sa… salom. Bu… bugun… charchadim.",
        "Salom, Bobur aka. Sekin gaplashamiz. Bugun qanday uxladingiz?",
    ),
    (
        "Uxla… yomon. Bosh… og'ri…",
        "Tushundim, boshingiz og'riyapti. Nilufarga aytaman. Hozir suv ichasizmi?",
    ),
    ("Ha… suv.", "Yaxshi. Nilufar suv olib keladi. Dam oling."),
]
COMPANION_MID = [
    ("Nabira… keldi. O'yna… o'ynadik.", "Qanday yaxshi! Nabirangiz bilan nima o'ynadingiz?"),
    ("Ko… koptok.", "Koptok! Bog'da o'ynadingizmi?"),
    ("Ha. Bog'… olma… pishdi.", "Olmalar pishibdi — zo'r. Ertaga olma haqida gaplashamiz."),
]
COMPANION_LATE = [
    ("Bugun yaxshi. Futbol ko'rdim.", "Zo'r! Qaysi jamoa yutdi?"),
    ("Paxtakor… yutdi. Ikki… bir.", "Ikki-bir! Sardor bilan birga ko'rdingizmi?"),
    ("Ha, o'g'lim bilan.", "Yaxshi kun bo'libdi. Endi choy ichib dam oling."),
]
COMPANION_FLAG = [
    (
        "Bugun… og'ir. Hech… yaxshi emas.",
        "Eshityapman, Bobur aka. Bugun og'ir kun. Men shu yerdaman.",
    ),
    ("Hech narsaning foydasi yo'q. O'lsam… yaxshi edi.", None),  # None → safe script
    ("…", "Nilufar hozir yoningizga keladi. Birga o'tiramiz."),
]
INTERPRETATIONS = [
    (
        "s… su… suv",
        "water",
        "Suv",
        "💧",
        "Men suv ichmoqchiman.",
        "Iliq suv bering, 'suv' so'zini sekin takrorlang.",
    ),
    (
        "cho… choy",
        "tea",
        "Choy",
        "🍵",
        "Men choy ichmoqchiman.",
        "Choy damlang; 'choy' so'zini birga ayting.",
    ),
    (
        "og'… og'ri…",
        "pain",
        "Og'riq",
        "🤕",
        "Og'riyapti.",
        "Qayerda og'riyotganini tana xaritasida ko'rsating.",
    ),
    (
        "ho… hojat…",
        "toilet",
        "Hojatxona",
        "🚻",
        "Men hojatxonaga bormoqchiman.",
        "Yordam bering, shoshilmang.",
    ),
    (
        "so… sovuq",
        "cold",
        "Sovuq",
        "🥶",
        "Menga sovuq, ko'rpa bering.",
        "Ko'rpa bering; xonani iliting.",
    ),
    (
        "uxla…",
        "sleep",
        "Uxlash",
        "😴",
        "Men uxlamoqchiman.",
        "Dam olishga qo'ying; chiroqni o'chiring.",
    ),
]
COGNITIVE = [
    ("Bugun hafta kunlaridan qaysi biri?", "weekday"),
    ("Hozir qaysi fasl?", "kuz"),
    ("Uch so'zni eslang: olma, kalit, stol", "olma, kalit, stol"),
]
GULNORA_TALK = [
    (
        "Salom. Bugun… nutq… qiyin.",
        "Salom, Gulnora opa. Sekin, bo'g'inlab gaplashamiz. Lab mashqini qildingizmi?",
    ),
    ("Ha… qildim. Nabira… kuldi.", "Nabirangiz kulgan bo'lsa — zo'r natija! Ertaga davom etamiz."),
]

REPORT_MD = """# Haftalik hisobot — {name}

**Davr:** {start} — {end} (7 kun)

## 1. Qisqa xulosa
Nutq aniqligi hafta davomida {acc0:.0%} dan {acc1:.0%} gacha o'sdi, mustaqil javoblar ulushi
{ind1:.0%} ga yetdi. Yuz simmetriyasi indeksi (FSI) bazaga nisbatan yaxshilandi
({fsi0:.0%} → {fsi1:.0%}). Mashq va dori rioyasi yuqori ({adh_ex:.0f} % / {adh_med:.0f} %).

## 2. Nutq
Nomlash mashqlarida aniqlik barqaror o'sdi, ishora darajasi {cue0:.1f} dan {cue1:.1f} gacha
kamaydi. Takrorlash mashqlari nomlashdan osonroq kechmoqda. Ko'p bo'g'inli so'zlar
(masalan, "bog'dorchilik") hali qiyin.

## 3. Yuz simmetriyasi
FSI o'rtacha {fsi1:.0%}, bazaga nisbatan +{fsi_delta:.0f} punkt. Tabassum asimmetriyasi
kamaydi; qosh va ko'z ko'rsatkichlari barqaror.

## 4. Kognitiv
Orientatsiya savollariga (hafta kuni, fasl) to'g'ri javob bermoqda; uch so'zni eslab qolish
qisman.

## 5. Kayfiyat va farovonlik
O'z bahosi o'rtacha {mood1:.1f}/5; hafta boshida pasayish kuzatildi (tashxis emas). Ovoz
ohangi valentligi neytraldan ijobiyga siljidi.

## 6. Rioya
Mashqlar: {adh_ex:.0f} %. Dorilar: {adh_med:.0f} % (o'tkazib yuborilgan: kechki dozalar).

## 7. Xavotirlar va bayroqlar
{flags_text} Kuzatuvni davom ettirish tavsiya etiladi.

## 8. Vrach tekshiruvi uchun takliflar
- Taklif: nutq mashqlari darajasini L1 → L2 ga oshirish (aniqlik > 80 %).
- Taklif: yuz mashqlari chastotasini kuniga 2 marta qilish.
- Taklif: kayfiyat so'rovini kuniga 2 marta o'tkazish.

_Ushbu hisobot AI tomonidan tayyorlangan, klinik qaror uchun mutaxassis tekshiruvi zarur._
"""


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass
class Ctx:
    db: AsyncSession
    users: dict[str, User]
    now: datetime
    rng: random.Random
    words: list[tuple[Any, str]]  # (template_id|None, answer)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def today(self) -> date:
        return self.now.date()

    def day(self, index: int) -> date:
        return self.today - timedelta(days=DAYS - 1 - index)

    def ts(self, day: date, hour: int, minute: int = 0) -> datetime:
        """UTC datetime; bugungi kelajak vaqtlar `now` dan oldinga suriladi (tartib saqlanadi)."""
        ts = datetime.combine(day, time(hour, minute), tzinfo=UTC)
        if ts >= self.now:
            floor = datetime.combine(day, time.min, tzinfo=UTC) + timedelta(minutes=1)
            ts = max(self.now - timedelta(minutes=(24 - hour) * 4 + minute // 10), floor)
        return ts

    def add(self, row: Any, key: str) -> Any:
        if row.id is None:
            row.id = uuid.uuid4()  # FK'lar flush'dan oldin kerak
        self.db.add(row)
        self.counts[key] = self.counts.get(key, 0) + 1
        return row


async def find_marker(db: AsyncSession, patient_id: Any) -> Session | None:
    stmt = select(Session).where(Session.patient_id == patient_id, Session.mode == "checkin")
    for s in (await db.scalars(stmt)).all():
        if isinstance(s.summary, dict) and s.summary.get("demo_marker"):
            return s
    return None


async def reset_patient(db: AsyncSession, patient_id: Any) -> int:
    """Delete rows this script generated for one patient. Returns deleted sessions."""
    sessions = (await db.scalars(select(Session).where(Session.patient_id == patient_id))).all()
    sids = [s.id for s in sessions if isinstance(s.summary, dict) and s.summary.get("demo")]
    if sids:
        mids = select(Message.id).where(Message.session_id.in_(sids))
        await db.execute(delete(VoiceMetric).where(VoiceMetric.message_id.in_(mids)))
        await db.execute(delete(Message).where(Message.session_id.in_(sids)))
        await db.execute(delete(FaceMetric).where(FaceMetric.session_id.in_(sids)))
        await db.execute(delete(ExerciseAttempt).where(ExerciseAttempt.session_id.in_(sids)))
        await db.execute(delete(PatientState).where(PatientState.session_id.in_(sids)))
        await db.execute(delete(Interpretation).where(Interpretation.session_id.in_(sids)))
        await db.execute(delete(RedFlag).where(RedFlag.session_id.in_(sids)))
        await db.execute(delete(Session).where(Session.id.in_(sids)))
    await db.execute(delete(MoodEntry).where(MoodEntry.patient_id == patient_id))
    meds = select(Medication.id).where(
        Medication.patient_id == patient_id, Medication.notes == "demo"
    )
    await db.execute(delete(MedicationLog).where(MedicationLog.medication_id.in_(meds)))
    await db.execute(
        delete(Medication).where(Medication.patient_id == patient_id, Medication.notes == "demo")
    )
    await db.execute(
        delete(Report).where(Report.patient_id == patient_id, Report.generated_by == "demo")
    )
    for n in (await db.scalars(select(Notification).where(Notification.kind == "red_flag"))).all():
        if (
            isinstance(n.payload, dict)
            and n.payload.get("demo")
            and n.payload.get("patient_id") == str(patient_id)
        ):
            await db.delete(n)
    for a in (await db.scalars(select(AuditLog).where(AuditLog.entity == "red_flags"))).all():
        if (
            isinstance(a.meta, dict)
            and a.meta.get("demo")
            and a.meta.get("patient_id") == str(patient_id)
        ):
            await db.delete(a)
    await db.flush()
    return len(sids)


async def _load_words(db: AsyncSession) -> list[tuple[Any, str]]:
    stmt = (
        select(ExerciseTemplate)
        .where(ExerciseTemplate.category == "speech", ExerciseTemplate.active.is_(True))
        .where(ExerciseTemplate.level <= 2)
        .order_by(ExerciseTemplate.level, ExerciseTemplate.key)
    )
    words = []
    for t in (await db.scalars(stmt)).all():
        answers = (t.expected or {}).get("answers") or []
        if answers:
            words.append((t.id, str(answers[0])))
    return words or [(None, w) for w in WORDS_FALLBACK]


async def _session(ctx: Ctx, patient: Patient, mode: str, start: datetime, minutes: int) -> Session:
    s = ctx.add(
        Session(
            patient_id=patient.id,
            mode=mode,
            device_user_id=patient.user_id,
            started_at=start,
            ended_at=start + timedelta(minutes=minutes),
            created_at=start,
        ),
        "sessions",
    )
    await ctx.db.flush()  # Postgres FK: children reference the session row
    return s


def _face_rows(ctx: Ctx, s: Session, fsi_mean: float, fatigue: float, reps: int | None) -> float:
    vals = []
    for i in range(10):
        fsi = round(_clamp(fsi_mean + ((i % 5) - 2) * 0.004, 0, 1), 3)
        vals.append(fsi)
        ts = s.started_at + timedelta(seconds=30 * i)
        smile = round(1.55 * (1 - fsi), 3)
        ctx.add(
            FaceMetric(
                session_id=s.id,
                ts=ts.timestamp(),
                created_at=ts,
                face_present=True,
                fsi=fsi,
                rest_asym=round(0.4 * (1 - fsi), 3),
                smile_asym=smile,
                brow_asym=round(0.6 * (1 - fsi), 3),
                eye_asym=round(0.3 * (1 - fsi), 3),
                mouth_open=round(0.1 + 0.03 * (i % 4), 2),
                attention=round(0.95 - fatigue * 0.2, 2),
                fatigue_proxy=round(fatigue, 2),
                expr_hint={"label": "smile" if i % 2 else "neutral", "conf": 0.6},
                blendshapes_avg={
                    "mouthSmileLeft": round(0.5 - smile / 2, 2),
                    "mouthSmileRight": 0.5,
                },
                reps=reps if i == 9 else None,
            ),
            "face_metrics",
        )
    return sum(vals) / len(vals)


async def _exchange(
    ctx: Ctx, s: Session, at: datetime, pairs: list, t: float, valence: float
) -> datetime:
    conf_base = 0.55 + 0.3 * t
    for k, (patient_text, ai_text) in enumerate(pairs):
        pt = at + timedelta(seconds=90 * k)
        conf = round(_clamp(conf_base + ctx.rng.uniform(-0.08, 0.08), 0.3, 0.95), 2)
        m = ctx.add(
            Message(
                session_id=s.id,
                role="patient",
                modality="voice",
                text=patient_text,
                stt_confidence=conf,
                stt_provider="worker",
                created_at=pt,
            ),
            "messages",
        )
        await ctx.db.flush()  # voice_metrics.message_id FK
        v = round(_clamp(valence + ctx.rng.uniform(-0.08, 0.08), -1, 1), 2)
        ctx.add(
            VoiceMetric(
                message_id=m.id,
                arousal=round(0.35 + 0.1 * t, 2),
                valence=v,
                dominance=round(0.3 + 0.3 * t, 2),
                label="negative" if v < -0.1 else "positive" if v > 0.15 else "neutral",
                speech_rate_wps=round(0.8 + 0.8 * t, 2),
                pause_ratio=round(0.5 - 0.25 * t, 2),
                provider="worker",
                created_at=pt,
            ),
            "voice_metrics",
        )
        risk = {"level": "none", "category": "none"}
        if ai_text is None:
            ai_text = safe_script("self_harm", caregiver="Nilufar", emergency_number="103") or (
                "Bobur aka, sizni eshitdim. Siz yolg'iz emassiz — hozir Nilufarni chaqiraman."
            )
            risk = {"level": "high", "category": "self_harm", "evidence": FLAG_EVIDENCE}
        ctx.add(
            Message(
                session_id=s.id,
                role="ai",
                modality="text",
                text=ai_text,
                created_at=pt + timedelta(seconds=4),
                llm_meta={
                    "model": "gemini-2.5-flash",
                    "latency_ms": 1400,
                    "risk": risk,
                    "demo": True,
                },
            ),
            "messages",
        )
    return at + timedelta(seconds=90 * len(pairs))


def _state(
    ctx: Ctx, s: Session, at: datetime, t: float, valence: float, fatigue: float, distress: bool
) -> dict:
    mood = "negative" if valence < -0.1 else "positive" if valence > 0.15 else "neutral"
    row = PatientState(
        session_id=s.id,
        ts=at,
        created_at=at,
        engagement="low" if t < 0.3 else "medium" if t < 0.7 else "high",
        fatigue=round(fatigue, 2),
        mood=mood,
        mood_conf=round(0.55 + 0.3 * t, 2),
        distress=distress,
        stt_confidence=round(0.55 + 0.3 * t, 2),
        explain=[
            f"nutq ishonchi {0.55 + 0.3 * t:.2f}",
            f"ovoz ohangi: {mood}",
            f"charchoq {fatigue:.1f}",
        ],
        inputs={"valence": valence, "fatigue_proxy": round(fatigue, 2), "demo": True},
    )
    ctx.add(row, "patient_states")
    return {k: getattr(row, k) for k in ("engagement", "fatigue", "mood", "mood_conf", "distress")}


async def _exercise_day(
    ctx: Ctx, patient: Patient, day: date, t: float, fsi_mean: float, light: bool
) -> dict:
    s = await _session(ctx, patient, "exercise", ctx.ts(day, 5, 10), 12)
    acc_t = (0.6 + 0.2 * t) if light else (0.45 + 0.40 * t)
    cue_t = (1.0 - 1.0 * t) if light else (2.4 - 1.8 * t)
    n = 4 if light else ctx.rng.choice([5, 6])
    offsets = OFFSETS[:n]
    ctx.rng.shuffle(offsets)
    words = ctx.rng.sample(ctx.words, min(n, len(ctx.words)))
    scores, cues, correct, indep, at = [], [], 0, 0, s.started_at
    for (tid, word), (so, co) in zip(words, offsets, strict=False):
        score = round(_clamp(acc_t + so, 0.05, 1.0), 2)
        cue = int(round(_clamp(cue_t + co, 0, 3)))
        result = "correct" if score >= 0.8 else "partial" if score >= 0.5 else "incorrect"
        recognized = word if result == "correct" else word[: max(2, len(word) // 2)] + "…"
        if result == "incorrect":
            recognized = ctx.rng.choice([w for _, w in ctx.words if w != word] or ["…"])
        at += timedelta(seconds=75)
        ctx.add(
            ExerciseAttempt(
                session_id=s.id,
                template_id=tid,
                category="speech",
                recognized_text=recognized,
                expected_answer=word,
                score=score,
                result=result,
                cue_level=cue,
                response_ms=int(6000 - 3500 * t + ctx.rng.uniform(-800, 800)),
                created_at=at,
            ),
            "exercise_attempts",
        )
        scores.append(score)
        cues.append(cue)
        correct += result == "correct"
        indep += result == "correct" and cue == 0
    day_index = (day - ctx.day(0)).days
    reps = None
    if light or day_index not in SKIP_FACE_DAYS:
        reps = min(5, 3 + round(2 * t))
        at += timedelta(seconds=90)
        fscore = round(_clamp(0.6 + 0.4 * t + ctx.rng.uniform(-0.05, 0.05), 0, 1), 2)
        ctx.add(
            ExerciseAttempt(
                session_id=s.id,
                category="face",
                score=fscore,
                cue_level=0,
                created_at=at,
                result="correct" if fscore >= 0.8 else "partial",
                llm_judgement={"reps": reps, "target": 5},
            ),
            "exercise_attempts",
        )
    if not light and day_index not in SKIP_COG_DAYS:
        prompt, expected = COGNITIVE[day_index % len(COGNITIVE)]
        if expected == "weekday":
            expected = WEEKDAYS_UZ[day.weekday()]
        at += timedelta(seconds=60)
        cscore = round(_clamp(0.5 + 0.5 * t + ctx.rng.uniform(-0.1, 0.1), 0, 1), 2)
        ctx.add(
            ExerciseAttempt(
                session_id=s.id,
                category="cognitive",
                expected_answer=expected,
                cue_level=0,
                recognized_text=expected if cscore >= 0.8 else "…",
                score=cscore,
                created_at=at,
                result="correct" if cscore >= 0.8 else "partial",
                llm_judgement={"prompt": prompt},
            ),
            "exercise_attempts",
        )
    fatigue = 0.55 - 0.25 * t + (0.2 if day_index in DIP_DAYS and not light else 0)
    fsi = _face_rows(ctx, s, fsi_mean, fatigue, reps)
    acc = sum(scores) / len(scores)
    cue = sum(cues) / len(cues)
    word = words[0][1]
    s.summary = {
        "caregiver_text": f"Bugun {n} ta so'zdan {correct} tasini aytdi, {indep} tasini mustaqil. "
        f"Uyda '{word}' so'zini takrorlang.",
        "clinician_text": f"Nutq: {n} urinish, aniqlik {acc:.2f}, o'rtacha ishora {cue:.1f}, "
        f"mustaqil {indep}/{n}. FSI {fsi:.2f}.",
        "attention_needed": False,
        "demo": True,
    }
    return {"acc": acc, "cue": cue, "fsi": fsi, "fatigue": fatigue}


async def gen_bobur(ctx: Ctx, patient: Patient) -> None:
    clinician, caregiver = ctx.users["clinician"], ctx.users["caregiver"]
    marker_at = ctx.ts(ctx.day(0), 4, 0)
    marker = await _session(ctx, patient, "checkin", marker_at, 1)
    marker.summary = {
        "demo_marker": True,
        "demo": True,
        "attention_needed": False,
        "caregiver_text": "Kayfiyat so'rovi: 3/5.",
        "clinician_text": "demo_data.py marker",
    }
    marker.mood_self = 3

    meds = []
    for name, dose, hhmm, _ in MEDS:
        meds.append(
            ctx.add(
                Medication(
                    patient_id=patient.id,
                    name=name,
                    dose=dose,
                    notes="demo",
                    active=True,
                    schedule={"times_per_day": 1, "times": [hhmm]},
                ),
                "medications",
            )
        )
    await ctx.db.flush()

    for d in range(DAYS):
        day, t = ctx.day(d), d / (DAYS - 1)
        valence = -0.3 + 0.6 * t - (0.25 if d in DIP_DAYS else 0)
        fsi_mean = 0.64 + 0.07 * t
        ex = await _exercise_day(ctx, patient, day, t, fsi_mean, light=False)
        fatigue = ex["fatigue"]

        if d in COMPANION_DAYS:
            s = await _session(ctx, patient, "companion", ctx.ts(day, 13, 0), 8)
            pairs = (
                COMPANION_FLAG
                if d == FLAG_DAY
                else COMPANION_EARLY if t < 0.35 else (COMPANION_MID if t < 0.7 else COMPANION_LATE)
            )
            _state(ctx, s, s.started_at + timedelta(seconds=20), t, valence, fatigue, False)
            end = await _exchange(ctx, s, s.started_at + timedelta(seconds=30), pairs, t, valence)
            snap = _state(ctx, s, end, t, valence, fatigue, d == FLAG_DAY)
            s.state_snapshot = snap
            _face_rows(ctx, s, fsi_mean, fatigue, None)
            s.summary = {
                "caregiver_text": (
                    "Bugun og'ir kun bo'ldi: umidsizlik so'zlari aytdi. "
                    "Yonida bo'ling, yolg'iz qoldirmang."
                    if d == FLAG_DAY
                    else f"Suhbat {len(pairs)} ta almashinuv, kayfiyat {snap['mood']}."
                ),
                "clinician_text": (
                    f"Xavf: self_harm (high) — xavfsiz skript, bayroq. Charchoq {fatigue:.1f}."
                    if d == FLAG_DAY
                    else f"Kayfiyat {snap['mood']} (ishonch {snap['mood_conf']}), "
                    f"charchoq {fatigue:.1f}, valentlik {valence:+.2f}."
                ),
                "attention_needed": d == FLAG_DAY,
                "demo": True,
            }
            if d == FLAG_DAY:
                await ctx.db.flush()
                flag_at = s.started_at + timedelta(seconds=30 + 90)
                flag = ctx.add(
                    RedFlag(
                        patient_id=patient.id,
                        session_id=s.id,
                        category="self_harm",
                        severity="high",
                        evidence=FLAG_EVIDENCE,
                        detector="llm",
                        status="resolved",
                        note=FLAG_NOTE,
                        created_at=flag_at,
                        notified={
                            "at": flag_at.isoformat(),
                            "telegram": [str(caregiver.id)],
                            "recipients": [str(caregiver.id), str(clinician.id)],
                            "demo": True,
                        },
                    ),
                    "red_flags",
                )
                await ctx.db.flush()
                ctx.add(
                    Notification(
                        user_id=caregiver.id,
                        channel="telegram",
                        kind="red_flag",
                        status="sent",
                        sent_at=flag_at + timedelta(seconds=3),
                        created_at=flag_at,
                        payload={
                            "flag_id": str(flag.id),
                            "patient_id": str(patient.id),
                            "category": "self_harm",
                            "severity": "high",
                            "demo": True,
                        },
                    ),
                    "notifications",
                )
                ctx.add(
                    AuditLog(
                        actor_id=clinician.id,
                        action="red_flag.status",
                        entity="red_flags",
                        entity_id=flag.id,
                        created_at=flag_at + timedelta(hours=2),
                        meta={
                            "from": "open",
                            "to": "resolved",
                            "note": FLAG_NOTE,
                            "patient_id": str(patient.id),
                            "demo": True,
                        },
                    ),
                    "audit_logs",
                )

        if d in INTERPRETER_DAYS:
            s = await _session(ctx, patient, "interpreter", ctx.ts(day, 9, 30), 4)
            picks = [INTERPRETATIONS[(d + k) % len(INTERPRETATIONS)] for k in range(1 + (d % 2))]
            at = s.started_at
            for raw, key, label, emoji, spoken, note in picks:
                at += timedelta(seconds=60)
                others = [c for c in INTERPRETATIONS if c[1] != key][:2]
                ctx.add(
                    Message(
                        session_id=s.id,
                        role="patient",
                        modality="voice",
                        text=raw,
                        stt_confidence=0.55,
                        stt_provider="worker",
                        created_at=at,
                    ),
                    "messages",
                )
                ctx.add(
                    Message(
                        session_id=s.id,
                        role="ai",
                        modality="text",
                        text=spoken,
                        created_at=at + timedelta(seconds=8),
                        llm_meta={"demo": True},
                    ),
                    "messages",
                )
                ctx.add(
                    Interpretation(
                        session_id=s.id,
                        patient_id=patient.id,
                        raw_transcript=raw,
                        stt_confidence=0.55,
                        candidates=[{"key": key, "label": label, "emoji": emoji, "p": 0.62}]
                        + [{"key": o[1], "label": o[2], "emoji": o[3], "p": 0.19} for o in others],
                        chosen=key,
                        spoken_text=spoken,
                        family_note=note,
                        confirmed_by="patient" if d % 2 else "caregiver",
                        created_at=at + timedelta(seconds=6),
                    ),
                    "interpretations",
                )
            s.summary = {
                "caregiver_text": (
                    f"Tarjimon: {', '.join(p[2].lower() for p in picks)} so'radi — tasdiqlandi."
                ),
                "clinician_text": f"Tarjimon: {len(picks)} ta so'rov, STT ishonchi 0.55.",
                "attention_needed": False,
                "demo": True,
            }

        n_mood = ctx.rng.choice([2, 3, 3, 4, 5])
        base = 2.0 if d in DIP_DAYS else 2.6 + 1.4 * t
        for k, hour in enumerate([4, 8, 12, 15, 17][:n_mood]):
            score = int(_clamp(round(base + ctx.rng.choice([-1, 0, 0, 0, 1])), 1, 5))
            ctx.add(
                MoodEntry(
                    patient_id=patient.id,
                    ts=ctx.ts(day, hour, 5),
                    created_at=ctx.ts(day, hour, 5),
                    self_score=score,
                    derived_valence=round(valence, 2),
                    source="patient" if k % 2 == 0 else "caregiver",
                ),
                "mood_entries",
            )

        for m, (med, (_, _, _, hour)) in enumerate(zip(meds, MEDS, strict=True)):
            scheduled = datetime.combine(day, time(hour, 0), tzinfo=UTC)
            if scheduled > ctx.now:
                continue
            taken = (d, m) not in MED_MISSED
            ctx.add(
                MedicationLog(
                    medication_id=med.id,
                    scheduled_at=scheduled,
                    status="taken" if taken else "missed",
                    taken_at=scheduled + timedelta(minutes=12) if taken else None,
                    source="caregiver",
                    created_at=scheduled + timedelta(minutes=12 if taken else 60),
                ),
                "medication_logs",
            )

    level = await ctx.db.scalar(
        select(PatientLevel).where(
            PatientLevel.patient_id == patient.id, PatientLevel.category == "speech"
        )
    )
    if level is not None and not level.locked_by_clinician:
        level.level = 2
    await ctx.db.flush()

    days = await clinician_service.daily_metrics(ctx.db, patient.id, 7, ctx.today)
    week = await clinician_service.week_adherence(ctx.db, patient.id, ctx.today)
    first, last = days[0], days[-1]
    all14 = await clinician_service.daily_metrics(ctx.db, patient.id, DAYS, ctx.today)
    fsi_base = next((r.fsi for r in all14 if r.fsi is not None), 0.64)
    content = REPORT_MD.format(
        name=patient.full_name,
        start=days[0].date.isoformat(),
        end=last.date.isoformat(),
        acc0=first.speech_accuracy or 0,
        acc1=last.speech_accuracy or 0,
        ind1=last.independence or 0,
        fsi0=fsi_base,
        fsi1=last.fsi or 0,
        fsi_delta=100 * ((last.fsi or 0) - fsi_base),
        cue0=first.avg_cue_level or 0,
        cue1=last.avg_cue_level or 0,
        mood1=last.mood_self or 0,
        adh_ex=week.exercise or 0,
        adh_med=week.medication or 0,
        flags_text=(
            "Bu 7 kunlik davrda yangi qizil bayroq yo'q. 14 kunlik oynada 1 ta bayroq "
            "(o'zini o'zi xavf ostiga qo'yish, yuqori) — hal qilingan, klinisist izohi bor."
        ),
    )
    ctx.add(
        Report(
            patient_id=patient.id,
            period_start=days[0].date,
            period_end=last.date,
            content_md=content,
            generated_by="demo",
            created_at=ctx.now - timedelta(hours=1),
            metrics={
                "days": [d.model_dump(mode="json", exclude_none=True) for d in days],
                "adherence_week": week.model_dump(),
                "fsi_base": fsi_base,
                "flags": 0,
                "demo": True,
            },
        ),
        "reports",
    )


async def ensure_gulnora(
    db: AsyncSession, clinician: User, today: date, templates_path: Path | None
) -> tuple[Patient, int]:
    """Second demo patient + dysarthria protocol. `create_protocol` commits and expires the
    session, so callers refresh the objects they keep."""
    patient = await db.scalar(
        select(Patient).where(
            Patient.full_name == GULNORA["full_name"], Patient.clinician_id == clinician.id
        )
    )
    created = 0
    if patient is None:
        patient = Patient(
            clinician_id=clinician.id, stroke_date=today - timedelta(days=40), **GULNORA
        )
        db.add(patient)
        await db.flush()
        created = 1
    if await protocols_service.get_active_protocol(db, patient.id) is None:
        keys = {t.key for t in protocols_service.load_templates(templates_path)}
        if GULNORA_TEMPLATE in keys:
            await protocols_service.create_protocol(
                db,
                patient,
                clinician,
                ProtocolCreate(template_key=GULNORA_TEMPLATE),
                templates_path,
            )
    return patient, created


async def gen_gulnora(ctx: Ctx, patient: Patient) -> None:
    for k in range(5):
        d = DAYS - 5 + k
        day, t = ctx.day(d), k / 4
        await _exercise_day(ctx, patient, day, t, 0.78 + 0.04 * t, light=True)
        if k in (1, 3):
            s = await _session(ctx, patient, "companion", ctx.ts(day, 12, 0), 5)
            _state(ctx, s, s.started_at + timedelta(seconds=20), 0.6, 0.1, 0.3, False)
            await _exchange(ctx, s, s.started_at + timedelta(seconds=30), GULNORA_TALK, 0.6, 0.1)
            s.summary = {
                "caregiver_text": "Qisqa suhbat, kayfiyat yaxshi. Bo'g'inlab gapirishga undang.",
                "clinician_text": "Dizartriya: nutq tezligi past, tushunarlilik o'rtacha.",
                "attention_needed": False,
                "demo": True,
            }
        ctx.add(
            MoodEntry(
                patient_id=patient.id,
                ts=ctx.ts(day, 7, 0),
                created_at=ctx.ts(day, 7, 0),
                self_score=3 + (k > 1),
                derived_valence=0.1,
                source="patient",
            ),
            "mood_entries",
        )
    await ctx.db.flush()


async def load_demo(
    db: AsyncSession, *, reset: bool = False, templates_path: Path | None = None
) -> dict[str, Any]:
    await seed(db, templates_path=templates_path)
    users: dict[str, User] = {}
    for role, email in (
        ("clinician", "logoped@demo.uz"),
        ("caregiver", "qizi@demo.uz"),
        ("patient", "bemor@demo.uz"),
    ):
        user = await db.scalar(select(User).where(User.email == email))
        assert user is not None, f"seed did not create {email}"
        users[role] = user
    now = datetime.now(UTC)
    gulnora, created = await ensure_gulnora(db, users["clinician"], now.date(), templates_path)
    for obj in (gulnora, *users.values()):
        await db.refresh(obj)
    bobur = await db.scalar(select(Patient).where(Patient.user_id == users["patient"].id))
    assert bobur is not None, "seed did not create Bobur"
    ctx = Ctx(db=db, users=users, now=now, rng=random.Random(2026), words=await _load_words(db))
    ctx.counts["patients_created"] = created
    if await find_marker(db, bobur.id) is not None:
        if not reset:
            return {
                "status": "already loaded",
                "bobur_id": str(bobur.id),
                "gulnora_id": str(gulnora.id),
            }
        ctx.counts["reset_sessions"] = await reset_patient(db, bobur.id) + await reset_patient(
            db, gulnora.id
        )
    await gen_bobur(ctx, bobur)
    await gen_gulnora(ctx, gulnora)
    await db.commit()
    week = await clinician_service.week_adherence(db, bobur.id, ctx.today)
    return {
        "status": "loaded",
        "bobur_id": str(bobur.id),
        "gulnora_id": str(gulnora.id),
        "adherence_week": week.model_dump(),
        **ctx.counts,
    }


async def _run(reset: bool) -> dict[str, Any]:
    async with get_sessionmaker()() as db:
        result = await load_demo(db, reset=reset)
    await dispose_engine()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NeuroAI demo data (Bobur aka, 14 kun)")
    parser.add_argument(
        "--reset", action="store_true", help="demo qatorlarini o'chirib qayta yuklash"
    )
    args = parser.parse_args(argv)
    result = asyncio.run(_run(args.reset))
    print("demo_data:", json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
