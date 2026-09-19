import pytest

from app.core.uz_text import normalize, number_forms, number_to_words, translit, variants


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Чой", "choy"),
        ("қўл", "qo'l"),
        ("Ўзбекистон", "o'zbekiston"),
        ("ғалаба", "g'alaba"),
        ("ҳаво", "havo"),
        ("цирк", "tsirk"),
        ("самолёт", "samolyot"),
        ("Ер", "yer"),  # е at word start → ye
        ("телефон", "telefon"),  # е inside a word → e
        ("Мен сув ичмоқчиман.", "men suv ichmoqchiman"),
    ],
)
def test_cyrillic_to_latin(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


@pytest.mark.parametrize("raw", ["oʻn", "o‘n", "o’n", "o'n", "o`n", "oʼn"])
def test_all_apostrophe_variants_collapse(raw: str) -> None:
    assert normalize(raw) == "o'n"


def test_lowercase_punctuation_and_spaces() -> None:
    assert normalize("  Salom,   DUNYO!!!  ") == "salom dunyo"
    assert normalize("Rahmat, yaxshi.") == "rahmat yaxshi"


def test_quoted_word_keeps_inner_apostrophe_only() -> None:
    assert normalize("'ko'z'") == "ko'z"
    assert normalize("ma’no") == "ma'no"


def test_empty_and_none() -> None:
    assert normalize("") == ""
    assert normalize(None) == ""
    assert normalize("!!!") == ""


def test_sheva_variants_applied() -> None:
    assert normalize("kartishka") == "kartoshka"
    assert normalize("tilifon") == "telefon"
    assert normalize("raxmat") == "rahmat"
    assert normalize("ogriyapti") == "og'riyapti"


def test_variants_dictionary_size_and_no_chains() -> None:
    table = variants()
    assert len(table) >= 50
    for value in table.values():
        assert value not in table, value  # canonical forms are never remapped again


def test_normalize_is_idempotent() -> None:
    for text in ("Kartishka!", "Чой", "oʻn ikki", "Boshim og‘riyapti"):
        once = normalize(text)
        assert normalize(once) == once


def test_number_words_to_digits_and_back() -> None:
    assert number_forms("ikki") == {"ikki", "2"}
    assert number_forms("2") == {"2", "ikki"}
    assert "bir ikki uch" in number_forms("1 2 3")
    assert "17" in number_forms("o'n yetti")
    assert "o'n yetti o'n to'rt" in number_forms("17 14")


def test_number_forms_cyrillic_and_tens() -> None:
    assert "20" in number_forms("йигирма")
    assert "45" in number_forms("qirq besh")
    assert number_to_words(0) == "nol"
    assert number_to_words(30) == "o'ttiz"
    assert number_to_words(100) is None


def test_translit_leaves_latin_untouched() -> None:
    assert translit("salom dunyo") == "salom dunyo"
