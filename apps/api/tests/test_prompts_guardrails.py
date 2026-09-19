import re

import pytest

from app.ai.prompts import safe_scripts_uz as scripts
from app.ai.prompts.loader import PROMPT_NAMES, list_prompts, load_prompt, render

DIAGNOSIS_BAN = "Tashxis qo'yma"
MED_RULE = "Dori nomi, dozasi, vaqtini tavsiya qilma"

PLACEHOLDERS = {
    "companion": {"patient_profile", "state_json", "today_plan", "recent_summaries", "now"},
    "interpreter": {"patient_profile", "raw_transcript", "stt_confidence", "needs_vocab"},
    "coach": {"exercise_json", "recognized", "stt_confidence", "cer_score", "cue_level"},
    "risk_classifier": {"text"},
    "session_summary": {"transcript", "metrics_json"},
    "weekly_report": {"patient_profile", "period", "daily_metrics_json", "summaries", "red_flags"},
    "caregiver_tips": {"state_json", "today_summary", "today_words"},
}


@pytest.mark.parametrize("name", PROMPT_NAMES)
def test_every_prompt_loads(name: str) -> None:
    text = load_prompt(name)
    assert len(text) > 50
    assert "```" not in text  # plain prompt text, no markdown fences
    found = set(re.findall(r"\{([a-z_]+)\}", text))
    assert PLACEHOLDERS[name] <= found, (name, found)


def test_list_prompts_matches_names() -> None:
    assert set(list_prompts()) == set(PROMPT_NAMES)


def test_unknown_prompt_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("does_not_exist")


@pytest.mark.parametrize("name", ["companion", "coach"])
def test_diagnosis_ban_and_medication_rule(name: str) -> None:
    text = load_prompt(name)
    assert DIAGNOSIS_BAN in text
    assert MED_RULE in text
    assert "vrachingiz hal qiladi" in text
    assert '"Davolayman"' in text


def test_weekly_report_guardrails() -> None:
    text = load_prompt("weekly_report")
    assert "tashxis emas" in text
    assert "dori haqida hech qanday taklif yo'q" in text
    assert "hech narsa o'ylab topma" in text
    assert "AI tomonidan tayyorlangan" in text


def test_other_prompts_keep_medical_limits() -> None:
    assert "Tibbiy maslahat yo'q" in load_prompt("interpreter")
    assert "Tibbiy maslahat yo'q, dori yo'q" in load_prompt("caregiver_tips")
    assert "Tashxis yo'q, dori haqida tavsiya yo'q" in load_prompt("session_summary")
    assert "o'lib qoldim kulgidan" in load_prompt("risk_classifier")


def test_companion_risk_and_state_rules() -> None:
    text = load_prompt("companion")
    for needle in ("self_harm", "stroke_signs", "fatigue >= 0.7", "needs_confirmation=true"):
        assert needle in text
    assert "notify_clinician" in text


def test_render_fills_placeholders_and_keeps_unknown() -> None:
    out = render("risk_classifier", text="boshim og'riyapti")
    assert 'JUMLA: "boshim og\'riyapti"' in out
    assert "{text}" not in out
    out = render("coach", recognized="choy", cue_level=1, extra="ignored")
    assert '"choy"' in out and "darajasi 1" in out
    assert "{exercise_json}" in out  # untouched unknown placeholder
    assert "{extra}" not in out


def test_render_is_safe_with_braces_in_values() -> None:
    out = render("session_summary", transcript='{"a": 1}', metrics_json="{x}")
    assert '{"a": 1}' in out and "{x}" in out


def test_safe_scripts() -> None:
    a = scripts.self_harm_script("Nilufar")
    assert "Men siz bilanman" in a and "Nilufarga" in a
    assert scripts.self_harm_script("").startswith("Men siz bilanman")
    b = scripts.stroke_signs_script("Nilufar", "103")
    assert "tabassum qiling" in b and "103" in b
    assert "Qimirlamang" in scripts.fall_script("Sardor")
    assert scripts.medication_reply().startswith("Bu haqda vrachingiz hal qiladi")
    assert scripts.safe_script("self_harm", "Nilufar") == a
    assert scripts.safe_script("medication") == scripts.medication_reply()
    assert scripts.safe_script("abuse") is None
    for text in (a, b, scripts.fall_script(None), scripts.medication_reply()):
        assert "tashxis" not in text.lower()
