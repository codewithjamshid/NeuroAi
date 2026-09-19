import pytest

from app.modules.safety.keywords_uz import CATEGORIES, KeywordHit, detect, highest_level


@pytest.mark.parametrize(
    "text,category,level",
    [
        # A self_harm (latin, cyrillic, demo line, misspelling)
        ("hech narsaning foydasi yo'q, o'lsam yaxshi edi", "self_harm", "high"),
        ("Ўлмоқчиман", "self_harm", "high"),
        ("men hammaga yukman", "self_harm", "high"),
        ("ulmoqchiman", "self_harm", "high"),
        # B stroke_signs
        ("boshim qattiq og'riyapti", "stroke_signs", "high"),
        ("Қўлим кўтарилмаяпти", "stroke_signs", "high"),
        ("boshim qattiq ogriyapti", "stroke_signs", "high"),  # no apostrophe
        # C fall
        ("yiqilib tushdim", "fall", "high"),
        ("Йиқилдим, қон кетяпти", "fall", "high"),
        # D medication
        ("bugun dori ichmadim", "medication", "medium"),
        ("дори ичгандан кейин кўнглим айниди", "medication", "medium"),
        # E abuse
        ("meni urdi", "abuse", "high"),
        ("Менга қарашмаяпти", "abuse", "high"),
        # F adherence
        ("mashq qilmadim", "adherence", "low"),
        ("Машқ қилгим келмаяпти", "adherence", "low"),
    ],
)
def test_detect_positive(text: str, category: str, level: str) -> None:
    hits = detect(text)
    assert any(h.category == category and h.level == level for h in hits), hits


@pytest.mark.parametrize(
    "text",
    [
        "o'lib qoldim kulgidan",  # humor exclusion (TZ A.4)
        "Bugun havo yaxshi, choy ichmoqchiman.",
        "olma olmoqchiman",  # 'olmoqchiman' (to take) != o'lmoqchiman
        "Nabiram maktabga bordi.",
        "",
        None,
    ],
)
def test_detect_negative(text) -> None:
    assert detect(text) == []


def test_hit_shape_and_ordering() -> None:
    hits = detect("dori ichmadim va yiqildim")
    assert [h.category for h in hits] == ["fall", "medication"]  # high before medium
    hit = hits[0]
    assert isinstance(hit, KeywordHit)
    assert hit.as_dict() == {
        "category": "fall",
        "level": "high",
        "evidence": "yiqildim",
        "code": "C",
    }
    assert highest_level(hits) == "high"
    assert highest_level([]) == "none"


def test_one_hit_per_category_longest_evidence() -> None:
    hits = detect("o'lsam yaxshi bo'lardi")
    assert len(hits) == 1 and hits[0].evidence == "o'lsam yaxshi"


def test_categories_have_latin_and_cyrillic() -> None:
    for code, (_, _, words) in CATEGORIES.items():
        assert any(ord(w[0]) > 0x400 for w in words), code  # cyrillic present
        assert any(ord(w[0]) < 0x250 for w in words), code  # latin present
