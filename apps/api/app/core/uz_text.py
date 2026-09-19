"""O'zbek matn normalizatsiyasi (TZ §7.1): kirill→lotin, apostrof, kichik harf, sheva, raqamlar."""

import json
import re
from functools import lru_cache
from pathlib import Path

SEEDS_DIR = Path(__file__).resolve().parents[1] / "seeds"
VARIANTS_FILE = SEEDS_DIR / "variants_uz.json"

_CYR_VOWELS = "аеёиоуэюяў"
_CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": "'", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}  # fmt: skip
_APOSTROPHES = "ʻʼ’‘`´ʹ‛′"
_NOT_WORD_RE = re.compile(r"[^\w']+|_")
_STRAY_APOS_RE = re.compile(r"(?<![a-z])'|'(?![a-z])")

_UNITS = {
    "nol": 0, "bir": 1, "ikki": 2, "uch": 3, "to'rt": 4, "besh": 5,
    "olti": 6, "yetti": 7, "sakkiz": 8, "to'qqiz": 9,
}  # fmt: skip
_TENS = {
    "o'n": 10, "yigirma": 20, "o'ttiz": 30, "qirq": 40, "ellik": 50,
    "oltmish": 60, "yetmish": 70, "sakson": 80, "to'qson": 90,
}  # fmt: skip
_UNIT_WORDS = {v: k for k, v in _UNITS.items()}
_TEN_WORDS = {v: k for k, v in _TENS.items()}


def translit(text: str) -> str:
    """Cyrillic → Latin (standard table); `е` → `ye` at word start / after a vowel."""
    out: list[str] = []
    prev = ""
    for ch in text:
        if ch == "е":
            out.append("ye" if (not prev.isalpha() or prev in _CYR_VOWELS) else "e")
        else:
            out.append(_CYR.get(ch, ch))
        prev = ch
    return "".join(out)


def _basic(text: str) -> str:
    text = translit(text.lower())
    for apo in _APOSTROPHES:
        text = text.replace(apo, "'")
    text = _NOT_WORD_RE.sub(" ", text)
    text = _STRAY_APOS_RE.sub("", text)
    return " ".join(text.split())


@lru_cache
def variants() -> dict[str, str]:
    """Sheva / spelling variant → canonical form, keys and values pre-normalized."""
    if not VARIANTS_FILE.is_file():
        return {}
    raw = json.loads(VARIANTS_FILE.read_text(encoding="utf-8"))
    return {_basic(k): _basic(v) for k, v in raw.items() if _basic(k) != _basic(v)}


def normalize(text: str | None) -> str:
    if not text:
        return ""
    table = variants()
    return " ".join(table.get(tok, tok) for tok in _basic(text).split())


def _to_digits(tokens: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _TENS:
            nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
            if nxt in _UNITS and _UNITS[nxt] > 0:
                out.append(str(_TENS[tok] + _UNITS[nxt]))
                i += 2
                continue
            out.append(str(_TENS[tok]))
        elif tok in _UNITS:
            out.append(str(_UNITS[tok]))
        else:
            out.append(tok)
        i += 1
    return out


def number_to_words(n: int) -> str | None:
    """0..99 → Uzbek words; None outside the range."""
    if n < 0 or n > 99:
        return None
    if n < 10:
        return _UNIT_WORDS[n]
    tens, unit = divmod(n, 10)
    return _TEN_WORDS[tens * 10] if unit == 0 else f"{_TEN_WORDS[tens * 10]} {_UNIT_WORDS[unit]}"


def _to_words(tokens: list[str]) -> list[str]:
    out: list[str] = []
    for tok in tokens:
        words = number_to_words(int(tok)) if tok.isdigit() and len(tok) <= 2 else None
        out.append(words if words is not None else tok)
    return out


def number_forms(text: str | None) -> set[str]:
    """All accepted spellings: as given, number words → digits, digits → number words."""
    norm = normalize(text)
    if not norm:
        return {""}
    tokens = norm.split()
    return {norm, " ".join(_to_digits(tokens)), " ".join(_to_words(tokens))}
