import pytest

from app.modules.exercises.scoring import (
    ScoreResult,
    adaptive_level,
    cer,
    next_cue,
    score_answer,
    session_metrics,
)

CHOY = ["choy", "чой"]
KARTOSHKA = ["kartoshka", "картошка"]


@pytest.mark.parametrize(
    "expected,recognized,value",
    [
        ("choy", "choy", 0.0),
        ("choy", "cho", 0.25),
        ("olma", "olmo", 0.25),
        ("choy", "chay", 0.0),  # sheva variant collapses via variants_uz.json
        ("Choy!", "чой", 0.0),
        ("", "", 0.0),
        ("", "x", 1.0),
    ],
)
def test_cer(expected: str, recognized: str, value: float) -> None:
    assert cer(expected, recognized) == pytest.approx(value)


@pytest.mark.parametrize(
    "answers,recognized,conf,result",
    [
        # exact / spelling
        (CHOY, "choy", 0.9, "correct"),
        (CHOY, "Choy.", 0.9, "correct"),
        (CHOY, "чой", 0.9, "correct"),  # kirill
        (CHOY, "ЧОЙ!", 0.9, "correct"),
        (CHOY, "chay", 0.9, "correct"),  # sheva variant via dictionary
        # apostrophe variants
        (["ko'z", "кўз"], "koʻz", 0.9, "correct"),
        (["ko'z", "кўз"], "ko‘z", 0.9, "correct"),
        (["ko'z", "кўз"], "ko’z", 0.9, "correct"),
        (["ko'z", "кўз"], "koz", 0.9, "correct"),  # missing apostrophe (variant dict)
        (["qo'l"], "қўл", 0.9, "correct"),
        # sheva / misspelling
        (KARTOSHKA, "kartishka", 0.9, "correct"),
        (KARTOSHKA, "картишка", 0.9, "correct"),
        (["telefon"], "tilifon", 0.9, "correct"),
        (["rahmat yaxshi"], "raxmat yahshi", 0.9, "correct"),
        (["og'riyapti"], "ogriyapti", 0.9, "correct"),
        # numbers
        (["bir ikki uch"], "1 2 3", 0.9, "correct"),
        (["1 2 3"], "bir ikki uch", 0.9, "correct"),
        (["17 14 11 8 5"], "o'n yetti o'n to'rt o'n bir sakkiz besh", 0.9, "correct"),
        (["o'n"], "10", 0.9, "correct"),
        # partial (first syllable / half word)
        (KARTOSHKA, "karto", 0.9, "partial"),
        (KARTOSHKA, "kartosh", 0.9, "correct"),  # 2 chars off 9 → 0.78
        (["telefon"], "tele", 0.9, "partial"),
        (["samolyot"], "samo", 0.9, "partial"),
        (["issiq choy"], "issiq", 0.9, "partial"),
        # incorrect
        (CHOY, "non", 0.9, "incorrect"),
        (KARTOSHKA, "non", 0.9, "incorrect"),
        (CHOY, "", 0.9, "incorrect"),
        (CHOY, None, 0.9, "incorrect"),
        # false-correct protection: exact match but low confidence
        (CHOY, "choy", 0.45, "partial"),
        (CHOY, "чой", 0.49, "partial"),
        # unclear: conf < 0.35
        (CHOY, "choy", 0.34, "unclear"),
        (CHOY, "xxx", 0.1, "unclear"),
        # no confidence given (text input) → plain CER
        (CHOY, "choy", None, "correct"),
        (KARTOSHKA, "karto", None, "partial"),
    ],
)
def test_score_answer_results(answers, recognized, conf, result) -> None:
    res = score_answer(answers, recognized, conf)
    assert isinstance(res, ScoreResult)
    assert res.result == result, res


def test_thresholds_exact_boundaries() -> None:
    # score = 1 - CER; 'kartosh' vs 'kartoshka' = 2/9 → 0.78 ≥ 0.75
    assert score_answer(KARTOSHKA, "kartosh", 0.9).score >= 0.75
    # 'karto' → 4/9 → 0.556 in [0.40, 0.75)
    res = score_answer(KARTOSHKA, "karto", 0.9)
    assert 0.40 <= res.score < 0.75 and res.first_syllable_ok


def test_best_expected_picks_matching_answer() -> None:
    res = score_answer(["mashina", "машина", "avtomobil"], "avtomabil", 0.9)
    assert res.best_expected == "avtomobil" and res.result == "correct"


def test_needs_llm_judge_rules() -> None:
    assert score_answer(CHOY, "choy", 0.9).needs_llm_judge is False
    assert score_answer(KARTOSHKA, "karto", 0.9).needs_llm_judge is True  # partial
    assert score_answer(CHOY, "non", 0.45).needs_llm_judge is True  # conf < 0.5
    assert score_answer(CHOY, "choy", 0.45).needs_llm_judge is True  # exact + low conf
    assert score_answer(CHOY, "non", 0.9).needs_llm_judge is False
    assert score_answer(CHOY, "choy", 0.2).needs_llm_judge is False  # unclear, not judged


def test_unclear_reason_and_score() -> None:
    res = score_answer(CHOY, "choy", 0.2)
    assert res.score == 0.0 and res.reason == "stt_conf_below_0.35"


def test_exact_low_conf_reason() -> None:
    assert score_answer(CHOY, "choy", 0.4).reason == "exact_match_low_conf"


def test_as_dict_has_contract_fields() -> None:
    d = score_answer(CHOY, "choy", 0.9).as_dict()
    assert {"score", "result", "best_expected", "needs_llm_judge", "reason"} <= set(d)


def test_next_cue_ladder() -> None:
    cues = {"semantic": "Bu ichiladi.", "phonemic": "cho…"}
    assert next_cue(0, cues) == (1, "Bu ichiladi.")
    assert next_cue(1, cues) == (2, "cho…")
    assert next_cue(2, cues, answer="choy") == (3, "Men aytaman, siz takrorlang: choy.")
    assert next_cue(3, cues) is None
    assert next_cue(0, None)[0] == 1  # fallback text when cues missing


@pytest.mark.parametrize(
    "history,level,expected",
    [
        (["correct", "correct", "correct"], 2, 3),
        ([("correct", 1), ("correct", 0), ("correct", 1)], 2, 3),
        ([("correct", 2), "correct", "correct"], 2, 2),  # cued (>1) does not count
        (["correct", "correct"], 2, 2),
        (["incorrect", "incorrect", "incorrect"], 3, 2),
        (["incorrect", "partial", "incorrect"], 3, 3),
        (["correct", "correct", "correct"], 5, 5),  # clamp top
        (["incorrect"] * 3, 1, 1),  # clamp bottom
        (["incorrect", "correct", "correct", "correct"], 1, 2),  # trailing window
        ([], 3, 3),
    ],
)
def test_adaptive_level(history, level, expected) -> None:
    assert adaptive_level(history, level) == expected


def test_session_metrics() -> None:
    attempts = [
        {"score": 1.0, "result": "correct", "cue_level": 0, "response_ms": 1000},
        {"score": 0.5, "result": "partial", "cue_level": 1, "response_ms": 3000},
        {"score": 1.0, "result": "correct", "cue_level": 2},
        {"score": 0.0, "result": "unclear", "cue_level": 0},
    ]
    m = session_metrics(attempts)
    assert m["attempts"] == 3
    assert m["accuracy"] == pytest.approx(0.833, abs=1e-3)
    assert m["independence"] == pytest.approx(0.333, abs=1e-3)
    assert m["avg_cue_level"] == 1.0
    assert m["avg_response_ms"] == 2000
    assert session_metrics([])["attempts"] == 0
