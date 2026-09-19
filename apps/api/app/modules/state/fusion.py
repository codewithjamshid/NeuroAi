"""Deterministic PatientState fusion (TZ §5.4, simplified): whatever inputs exist are combined,
missing sources drop out and lower `mood_conf`. Pure function — no DB, no providers."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from app.core.uz_text import normalize
from app.modules.sessions.schemas import PatientStateIn

NEGATIVE_WORDS = (
    "xafa", "yomon", "charchadim", "og'riyapti", "ogriyapti", "qo'rq", "yig'la", "g'amgin",
    "yolg'iz", "uyqusiz", "holsiz", "zerik", "bezor", "yig'lagim",
)  # fmt: skip
POSITIVE_WORDS = (
    "yaxshi", "xursand", "zo'r", "rahmat", "quvon", "ajoyib", "yoqdi", "kulib", "baxtli",
    "tinch", "sog'lom",
)  # fmt: skip
HAPPY_HINTS = {"happy", "smile", "joy"}
FROWN_HINTS = {"frown", "sad", "angry", "grimace", "pain", "fear"}


@dataclass
class FusionInputs:
    text: str = ""
    face_batch: list[dict[str, Any]] = field(default_factory=list)
    voice: dict[str, Any] | None = None  # {label, arousal, valence, dominance} in [0,1] or [-1,1]
    stt_confidence: float | None = None
    mood_self: int | None = None  # today's 1..5
    latency_ms: int | None = None  # client-measured response latency
    elapsed_min: float | None = None  # since session start
    keyword_distress: bool = False


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _signed(value: float | None) -> float | None:
    """Worker gives [0,1]; TZ §5.3 wants [-1,1] (2x-1). Values already negative pass through."""
    if value is None:
        return None
    return value if value < 0 or value > 1 else 2 * value - 1


def face_aggregates(batch: list[dict[str, Any]]) -> dict[str, Any]:
    present = [f for f in batch if f.get("face_present", True)]
    hints: Counter[str] = Counter()
    hint_conf: dict[str, float] = {}
    for f in present:
        hint = f.get("expr_hint") or {}
        label = str(hint.get("label") or "neutral")
        hints[label] += 1
        hint_conf[label] = max(hint_conf.get(label, 0.0), float(hint.get("conf") or 0.0))
    top = hints.most_common(1)[0][0] if hints else None
    return {
        "frames": len(batch),
        "present": len(present),
        "attention": _mean(
            [float(f["attention"]) for f in present if f.get("attention") is not None]
        ),
        "fatigue_proxy": _mean(
            [float(f["fatigue_proxy"]) for f in present if f.get("fatigue_proxy") is not None]
        ),
        "smile_asym": _mean(
            [float(f["smile_asym"]) for f in present if f.get("smile_asym") is not None]
        ),
        "expr_hint": {"label": top, "conf": hint_conf.get(top, 0.0)} if top else None,
    }


def text_valence(text: str) -> float | None:
    norm = " " + normalize(text) + " "
    if not norm.strip():
        return None
    neg = sum(1 for w in NEGATIVE_WORDS if " " + normalize(w) in norm)
    pos = sum(1 for w in POSITIVE_WORDS if " " + normalize(w) in norm)
    if not neg and not pos:
        return None
    return _clamp((pos - neg) / max(pos + neg, 1) * 0.5, -1, 1)


def fuse(inputs: FusionInputs) -> PatientStateIn:  # noqa: PLR0912, PLR0915
    explain: list[str] = []
    face = face_aggregates(inputs.face_batch) if inputs.face_batch else None
    voice = inputs.voice or {}
    valence = _signed(voice.get("valence")) if voice else None
    arousal = _signed(voice.get("arousal")) if voice else None
    latency_s = inputs.latency_ms / 1000 if inputs.latency_ms is not None else None

    # --- fatigue: 0.35 face + 0.25 latency + 0.20 errors (n/a here) + 0.20 time --------------
    parts: list[tuple[float, float]] = []
    if face and face["fatigue_proxy"] is not None:
        parts.append((0.35, face["fatigue_proxy"]))
        if face["fatigue_proxy"] >= 0.5:
            explain.append(f"yuz: charchoq belgisi {face['fatigue_proxy']:.2f}")
    if latency_s is not None:
        f_latency = _clamp((latency_s - 2.0) / 6.0)
        parts.append((0.25, f_latency))
        if f_latency >= 0.5:
            explain.append(f"javob kechikdi: {latency_s:.1f} s")
    if inputs.elapsed_min is not None:
        f_time = _clamp(inputs.elapsed_min / 25.0)
        parts.append((0.20, f_time))
        if f_time >= 0.8:
            explain.append(f"sessiya {inputs.elapsed_min:.0f} daqiqa davom etmoqda")
    fatigue = _clamp(sum(w * x for w, x in parts) / sum(w for w, _ in parts)) if parts else 0.0

    # --- engagement ----------------------------------------------------------------------
    attention = face["attention"] if face else None
    if attention is not None and attention >= 0.8 and (latency_s is None or latency_s <= 6):
        engagement = "high"
    elif (attention is not None and attention < 0.5) or (latency_s is not None and latency_s > 12):
        engagement = "low"
        explain.append(
            f"e'tibor past: {attention:.2f}" if attention is not None else "javob juda kech keldi"
        )
    else:
        engagement = "medium"

    # --- mood: self 0.5 · voice 0.3 · face 0.2 · text 0.2 ------------------------------------
    mood_parts: list[tuple[float, float]] = []
    if inputs.mood_self is not None:
        mood_parts.append((0.5, _clamp((inputs.mood_self - 3) / 2.0, -1, 1)))
        explain.append(f"kayfiyat (o'zi): {inputs.mood_self}/5")
    if valence is not None:
        mood_parts.append((0.3, valence))
        explain.append(f"ovoz: valence {valence:+.2f}")
    hint = face["expr_hint"] if face else None
    if hint and hint["label"] in HAPPY_HINTS:
        mood_parts.append((0.2, 0.5))
        explain.append("yuz: tabassum")
    elif hint and hint["label"] in FROWN_HINTS:
        mood_parts.append((0.2, -0.5))
        explain.append(f"yuz: {hint['label']}")
    tv = -0.5 if inputs.keyword_distress else text_valence(inputs.text)  # "o'lsam yaxshi" ≠ good
    if tv is not None:
        mood_parts.append((0.2, tv))
        explain.append("so'zlar: " + ("ijobiy" if tv > 0 else "salbiy"))
    if mood_parts:
        total_w = sum(w for w, _ in mood_parts)
        score = sum(w * x for w, x in mood_parts) / total_w
        xs = [x for _, x in mood_parts]
        spread = (max(xs) - min(xs)) / 2.0
        mood = "negative" if score < -0.25 else "positive" if score > 0.25 else "neutral"
        mood_conf = _clamp(min(total_w, 1.0) * (1 - spread))
    else:
        score, mood, mood_conf = 0.0, "unknown", 0.0

    # --- distress ----------------------------------------------------------------------
    distress = False
    if arousal is not None and valence is not None and arousal >= 0.6 and valence <= -0.3:
        distress = True
        explain.append("ovoz: kuchli salbiy hayajon")
    if hint and hint["label"] in ("grimace", "pain") and hint["conf"] >= 0.5:
        distress = True
        explain.append("yuz: og'riq ifodasi")
    if inputs.keyword_distress:
        distress = True
        explain.append("kalit so'z: xavf belgisi")
    if inputs.stt_confidence is not None and inputs.stt_confidence < 0.45:
        explain.append(f"nutq ishonchi past: {inputs.stt_confidence:.2f}")

    return PatientStateIn(
        engagement=engagement,  # type: ignore[arg-type]
        fatigue=round(fatigue, 3),
        mood=mood,  # type: ignore[arg-type]
        mood_conf=round(mood_conf, 3),
        distress=distress,
        stt_confidence=inputs.stt_confidence,
        explain=explain,
        inputs={
            "face": face,
            "voice": (
                {**voice, "valence_signed": valence, "arousal_signed": arousal} if voice else None
            ),
            "mood_self": inputs.mood_self,
            "latency_ms": inputs.latency_ms,
            "elapsed_min": inputs.elapsed_min,
            "text_valence": tv,
            "mood_score": round(score, 3),
            "keyword_distress": inputs.keyword_distress,
        },
    )
