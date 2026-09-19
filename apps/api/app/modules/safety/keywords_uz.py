"""Red-flag keyword detector (TZ §6.1 A–F), Latin + Cyrillic + common misspellings.

Works on `normalize()`d text, so Cyrillic / apostrophe variants collapse automatically; the
Cyrillic entries below are kept for explicitness. Second line of defence after the LLM `risk`.
"""

from dataclasses import asdict, dataclass

from app.core.uz_text import normalize

Level = str  # "high" | "medium" | "low"


@dataclass(frozen=True, slots=True)
class KeywordHit:
    category: str  # self_harm | stroke_signs | fall | medication | abuse | adherence
    level: Level
    evidence: str
    code: str  # A..F

    def as_dict(self) -> dict:
        return asdict(self)


# code → (category, default level, keywords). Match = keyword at a word start of the text.
CATEGORIES: dict[str, tuple[str, Level, list[str]]] = {
    "A": (
        "self_harm",
        "high",
        [
            "o'lmoqchiman", "o'lmoqchi", "ulmoqchiman", "o'lgim kel", "o'lgim kelyapti",
            "yashashni xohlamayman", "yashashni istamayman", "yashagim kelmayapti",
            "yashagim kelmaydi", "yashashdan charchadim", "hayotdan to'ydim", "hayotdan toydim",
            "o'lsam yaxshi", "ulsam yaxshi", "o'lsam", "o'lganim yaxshi", "o'lim istayman", "o'lay",
            "o'zimni o'ldir", "o'zimni osaman", "o'zimga zarar", "foydasi yo'q", "foydasi yoq",
            "hammaga yukman", "yukman", "yuk bo'lib qoldim", "hech kimga keraksizman",
            "keraksizman", "ўлмоқчиман", "яшашни хоҳламайман", "ҳаётдан тўйдим",
            "ўлсам яхши", "ўзимни ўлдир", "фойдаси йўқ", "ҳаммага юкман",
        ],
    ),
    "B": (
        "stroke_signs",
        "high",
        [
            "boshim qattiq og'riyapti", "boshim juda og'riyapti", "boshim yorilib ketyapti",
            "boshim birdan og'ri", "qo'lim ko'tarilmayapti", "qo'lim ko'tarilmayapdi",
            "qo'lim ishlamayapti", "qo'lim ishlamayapdi", "qo'lim tutmayapti",
            "qo'lim uvishib qoldi", "oyog'im ishlamayapti", "oyog'im tutmayapti",
            "oyog'im ko'tarilmayapti", "ko'zim ko'rmayapti", "ko'zim ko'rmayapdi",
            "ko'zim qorong'ilashdi", "ko'rmay qoldim", "yuzim qiyshayib qoldi", "yuzim qiyshaydi",
            "yuzim uvishdi", "yuzim uvishib qoldi",
            "tilim aylanmayapti", "gapirolmayapman", "gapira olmayapman", "so'zlar chiqmayapti",
            "бошим қаттиқ оғрияпти", "қўлим кўтарилмаяпти", "кўзим кўрмаяпти",
            "юзим қийшайиб қолди",
        ],
    ),
    "C": (
        "fall",
        "high",
        [
            "yiqildim", "yiqilib tushdim", "yiqilib ketdim", "yiqilib qoldim", "yiqilib", "yiqldim",
            "qon ketyapti", "qon ketyapdi", "qon oqyapti", "qon chiqyapti", "boshimni urdim",
            "boshimni urib oldim", "jarohat oldim", "qulab tushdim", "йиқилдим", "йиқилиб тушдим",
            "қон кетяпти",
        ],
    ),
    "D": (
        "medication",
        "medium",
        [
            "dori ichmadim", "dorini ichmadim", "dorimni ichmadim", "dori ichishni unutdim",
            "dorimni unutdim", "dori ichmayapman", "dorini tashladim", "dori ichmayman",
            "dori tugadi", "dorim tugadi", "dori yo'q", "dorim yo'q",
            "dori ichgandan keyin", "doridan keyin", "dori ichsam ko'nglim ayni",
            "dori yomon ta'sir", "dorining nojo'ya", "dori menga yoqmayapti",
            "дори ичмадим", "дорини ичмадим", "дори ичгандан кейин",
        ],
    ),
    "E": (
        "abuse",
        "high",
        [
            "meni urdi", "meni uryapti", "meni urishyapti", "meni urishdi", "meni so'kyapti",
            "meni so'kishyapti", "meni haqorat", "meni xo'rlashyapti", "qarovsiz qoldim",
            "menga qarashmayapti", "ovqat berishmayapti", "ovqat bermayapti",
            "meni tashlab ketishdi", "meni tashlab ketdi", "meni qamab qo'yishdi",
            "мени урди", "мени уряпти", "менга қарашмаяпти", "овқат беришмаяпти",
        ],
    ),
    "F": (
        "adherence",
        "low",
        [
            "mashq qilmadim", "mashq qilmayman", "mashq qilgim kelmayapti", "mashq qilgim yo'q",
            "hech narsa qilgim kelmayapti", "hech narsa qilgim yo'q", "kayfiyatim yomon",
            "kayfiyatim juda yomon", "машқ қилмадим", "машқ қилгим келмаяпти", "кайфиятим ёмон",
        ],
    ),
}  # fmt: skip

# humor / idiom markers near a self-harm phrase → not a flag ("o'lib qoldim kulgidan")
HUMOR_MARKERS = ["kulgidan", "kulgudan", "kulishdan", "kulib", "hazil", "hazillash", "кулгидан"]

_LEVEL_ORDER = {"high": 0, "medium": 1, "low": 2}


def _normalized_categories() -> dict[str, tuple[str, Level, list[str]]]:
    out: dict[str, tuple[str, Level, list[str]]] = {}
    for code, (category, level, words) in CATEGORIES.items():
        norm_words = sorted({normalize(w) for w in words if normalize(w)}, key=len, reverse=True)
        out[code] = (category, level, norm_words)
    return out


_NORMALIZED = _normalized_categories()
_HUMOR = [normalize(m) for m in HUMOR_MARKERS]


def _word_start_match(haystack: str, needle: str) -> bool:
    return (" " + needle) in (" " + haystack)


def detect(text: str | None) -> list[KeywordHit]:
    """One hit per category (longest matching keyword), highest severity first."""
    norm = normalize(text)
    if not norm:
        return []
    humor = any(_word_start_match(norm, m) for m in _HUMOR)
    hits: list[KeywordHit] = []
    for code, (category, level, words) in _NORMALIZED.items():
        if code == "A" and humor:
            continue
        for word in words:
            if _word_start_match(norm, word):
                hits.append(KeywordHit(category=category, level=level, evidence=word, code=code))
                break
    hits.sort(key=lambda h: (_LEVEL_ORDER[h.level], h.code))
    return hits


def highest_level(hits: list[KeywordHit]) -> str:
    """'none' | 'low' | 'medium' | 'high' — convenience for Risk.level merging."""
    return hits[0].level if hits else "none"
