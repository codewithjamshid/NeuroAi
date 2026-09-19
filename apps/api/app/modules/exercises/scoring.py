"""Speech scoring (TZ §7.2), cueing ladder and adaptive level (§7.5). Pure functions, no I/O."""

from dataclasses import asdict, dataclass
from typing import Literal

from rapidfuzz.distance import Levenshtein

from app.core.uz_text import normalize, number_forms

CORRECT_THRESHOLD = 0.75
PARTIAL_THRESHOLD = 0.40
UNCLEAR_CONF = 0.35  # below → not scored ("Eshitolmadim, yana bir bor")
LOW_CONF = 0.5  # below → LLM judge; exact match downgraded to partial
MAX_LEVEL = 5
MIN_LEVEL = 1
MAX_CUE = 3

ResultKind = Literal["correct", "partial", "incorrect", "unclear"]
MODEL_CUE_PREFIX = "Men aytaman, siz takrorlang"


@dataclass(slots=True)
class ScoreResult:
    score: float
    result: ResultKind
    best_expected: str
    needs_llm_judge: bool
    reason: str
    recognized_norm: str = ""
    first_syllable_ok: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def cer(expected: str, recognized: str) -> float:
    """CER = Levenshtein(norm(expected), norm(recognized)) / len(norm(expected))."""
    e, r = normalize(expected), normalize(recognized)
    if not e:
        return 0.0 if not r else 1.0
    return Levenshtein.distance(e, r) / len(e)


def _best_score(expected_answers: list[str], recognized: str) -> tuple[float, str, str]:
    """max over answers × number forms of (1 − CER); returns (score, best_expected, best_norm)."""
    rec_forms = number_forms(recognized)
    best, best_expected, best_norm = 0.0, expected_answers[0] if expected_answers else "", ""
    for answer in expected_answers:
        for exp_form in number_forms(answer):
            if not exp_form:
                continue
            for rec_form in rec_forms:
                score = 1.0 - min(cer(exp_form, rec_form), 1.0)
                if score > best:
                    best, best_expected, best_norm = score, answer, exp_form
    return best, best_expected, best_norm


def score_answer(
    expected_answers: list[str], recognized: str | None, stt_conf: float | None = None
) -> ScoreResult:
    rec_norm = normalize(recognized)
    if stt_conf is not None and stt_conf < UNCLEAR_CONF:
        return ScoreResult(0.0, "unclear", "", False, "stt_conf_below_0.35", rec_norm)
    if not expected_answers:
        return ScoreResult(0.0, "incorrect", "", False, "no_expected_answers", rec_norm)
    if not rec_norm:
        return ScoreResult(0.0, "incorrect", expected_answers[0], False, "empty_answer", rec_norm)

    score, best_expected, best_norm = _best_score(expected_answers, rec_norm)
    score = round(score, 4)
    low_conf = stt_conf is not None and stt_conf < LOW_CONF
    if score >= CORRECT_THRESHOLD:
        result: ResultKind = "correct"
        reason = "cer_correct"
    elif score >= PARTIAL_THRESHOLD:
        result, reason = "partial", "cer_partial"
    else:
        result, reason = "incorrect", "cer_incorrect"
    if score >= 1.0 and low_conf:
        result, reason = "partial", "exact_match_low_conf"  # soxta-to'g'ridan himoya
    first_syllable_ok = bool(best_norm) and rec_norm.startswith(best_norm[:2])
    return ScoreResult(
        score=score,
        result=result,
        best_expected=best_expected,
        needs_llm_judge=result == "partial" or low_conf,
        reason=reason,
        recognized_norm=rec_norm,
        first_syllable_ok=first_syllable_ok,
    )


def next_cue(cue_level: int, cues: dict | None, answer: str = "") -> tuple[int, str] | None:
    """Cueing ladder 0→1 semantic→2 phonemic→3 model; None when exhausted (cue_level ≥ 3)."""
    cues = cues or {}
    if cue_level <= 0:
        return 1, str(cues.get("semantic") or "Bu narsa nima uchun kerak? O'ylab ko'ring.")
    if cue_level == 1:
        return 2, str(cues.get("phonemic") or "Birinchi bo'g'inini ayting…")
    if cue_level == 2:
        text = f"{MODEL_CUE_PREFIX}: {answer}." if answer else f"{MODEL_CUE_PREFIX}."
        return 3, text
    return None


def _entry(item: str | tuple[str, int]) -> tuple[str, int]:
    if isinstance(item, tuple):
        return item[0], int(item[1])
    return item, 0


def adaptive_level(history: list[str | tuple[str, int]], level: int) -> int:
    """history = chronological results ("correct"|"partial"|"incorrect"|"unclear"|"skipped"),
    or (result, cue_level) tuples. 3 trailing correct with cue ≤ 1 → +1; 3 trailing incorrect → −1.
    """
    last = [_entry(h) for h in history[-3:]]
    if len(last) == 3:
        if all(r == "correct" and c <= 1 for r, c in last):
            level += 1
        elif all(r == "incorrect" for r, c in last):
            level -= 1
    return max(MIN_LEVEL, min(MAX_LEVEL, level))


def session_metrics(attempts: list[dict]) -> dict:
    """attempts: [{score, result, cue_level, response_ms?}] → accuracy/independence/avg_cue."""
    scored = [a for a in attempts if a.get("result") in ("correct", "partial", "incorrect")]
    if not scored:
        return {
            "accuracy": 0.0,
            "independence": 0.0,
            "avg_cue_level": 0.0,
            "avg_response_ms": 0,
            "attempts": 0,
        }
    n = len(scored)
    independent = sum(
        1 for a in scored if a["result"] == "correct" and int(a.get("cue_level", 0)) == 0
    )
    times = [a["response_ms"] for a in scored if a.get("response_ms") is not None]
    return {
        "accuracy": round(sum(float(a.get("score", 0)) for a in scored) / n, 3),
        "independence": round(independent / n, 3),
        "avg_cue_level": round(sum(int(a.get("cue_level", 0)) for a in scored) / n, 2),
        "avg_response_ms": int(sum(times) / len(times)) if times else 0,
        "attempts": n,
    }
