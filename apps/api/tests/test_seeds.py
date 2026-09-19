import json
from collections import Counter

import pytest

from app.core.uz_text import normalize
from app.seeds import SEEDS_DIR, load_seed

L1_WORDS = (
    "non suv choy olma uy it mushuk gul ko'z qo'l kitob osh tuz sut nok ot quyosh oy ona ota "
    "bola tish oyoq uzum tuxum qoshiq stol eshik soat kalit"
).split()

REQUIRED_COUNTS = {
    ("naming", 1): 30,
    ("naming", 2): 30,
    ("repetition", 1): 10,
    ("repetition", 2): 8,
    ("repetition", 3): 8,
    ("automatic", 1): 4,
}


@pytest.mark.parametrize(
    "name",
    [
        "exercises_uz",
        "face_exercises",
        "cognitive_uz",
        "needs_uz",
        "protocol_templates",
        "variants_uz",
    ],
)
def test_seed_files_are_valid_json(name: str) -> None:
    path = SEEDS_DIR / f"{name}.json"
    assert path.is_file()
    json.loads(path.read_text(encoding="utf-8"))
    assert load_seed(name)


def test_exercises_counts() -> None:
    items = load_seed("exercises_uz")
    assert len(items) >= 80
    counts = Counter((i["subtype"], i["level"]) for i in items)
    for key, minimum in REQUIRED_COUNTS.items():
        assert counts[key] >= minimum, (key, counts[key])
    assert sum(c for (s, _), c in counts.items() if s == "completion") >= 10
    assert sum(c for (s, _), c in counts.items() if s == "reading") >= 6


def test_exercises_schema_and_uniqueness() -> None:
    items = load_seed("exercises_uz")
    keys = [i["key"] for i in items]
    assert len(keys) == len(set(keys))
    combos = [
        (i["subtype"], i["level"], i["prompt_text"], json.dumps(i["stimulus"])) for i in items
    ]
    assert len(combos) == len(set(combos))
    for item in items:
        assert item["category"] == "speech"
        assert 1 <= item["level"] <= 5
        assert item["prompt_text"]
        assert item["stimulus"].get("emoji") or item["stimulus"].get("text")
        answers = item["expected"]["answers"]
        assert len(answers) >= 1 and all(normalize(a) for a in answers)
        assert item["cues"]["semantic"] and item["cues"]["phonemic"]
        assert item["cues"]["phonemic"].endswith("…")
        assert isinstance(item["tags"], list)


def test_naming_l1_has_all_tz_words_with_emoji() -> None:
    items = [i for i in load_seed("exercises_uz") if i["subtype"] == "naming" and i["level"] == 1]
    firsts = {i["expected"]["answers"][0] for i in items}
    assert set(L1_WORDS) <= firsts
    for item in items:
        assert item["stimulus"]["emoji"]
        assert len(item["expected"]["answers"]) >= 2  # latin + cyrillic


def test_cyrillic_answers_normalize_to_latin() -> None:
    for item in load_seed("exercises_uz"):
        answers = item["expected"]["answers"]
        if item["subtype"] in ("naming", "repetition", "reading"):
            assert normalize(answers[1]) == normalize(answers[0]), item["key"]


def test_face_exercises() -> None:
    items = load_seed("face_exercises")
    assert [i["key"] for i in items] == [
        "face_smile",
        "face_brows",
        "face_eyes",
        "face_pucker",
        "face_cheeks",
    ]
    for item in items:
        assert item["title"] and item["instruction"] and item["blendshape"]
        assert item["target_reps"] == 5 and item["hold_s"] == 3


def test_cognitive_items() -> None:
    items = load_seed("cognitive_uz")
    assert len(items) == 12
    assert len({i["key"] for i in items}) == 12
    subtypes = Counter(i["subtype"] for i in items)
    assert subtypes["orientation"] == 4 and subtypes["memory"] == 3
    assert all(i["category"] == "cognitive" and i["prompt_text"] for i in items)


def test_needs_vocab() -> None:
    data = load_seed("needs_uz")
    items = data["items"]
    keys = [i["key"] for i in items]
    assert len(keys) == 40 and len(set(keys)) == 40
    groups = {g["key"] for g in data["groups"]}
    assert groups == {"asosiy", "tana", "his", "oila", "javob"}
    for item in items:
        assert item["label"] and item["emoji"] and item["group"] in groups
        assert item["spoken"]
    for key in ("water", "pain", "medicine", "help", "doctor", "yes", "no"):
        assert key in keys
    assert data["person_template"]["key"].startswith("person:")
    assert [z["key"] for z in data["body_map"]] == ["head", "chest", "belly", "arm", "leg", "back"]
    assert [z["label"] for z in data["body_map"]] == [
        "Bosh",
        "Ko'krak",
        "Qorin",
        "Qo'l",
        "Oyoq",
        "Orqa",
    ]


def test_protocol_templates() -> None:
    templates = load_seed("protocol_templates")
    assert [t["key"] for t in templates] == [
        "motor_aphasia_m1",
        "sensory_aphasia_m1",
        "dysarthria_m1",
        "cognitive_focus",
    ]
    for tpl in templates:
        assert tpl["title"] and tpl["description"]
        assert tpl["medications"] == []
        assert len(tpl["items"]) >= 3
        for item in tpl["items"]:
            assert item["kind"] in ("exercise", "medication", "checkin")
            freq = item["frequency"]
            assert freq["times_per_day"] == len(freq["times"]) >= 1
            assert freq["days"] == [1, 2, 3, 4, 5, 6, 7]
            assert item["duration_min"] >= 1
            assert 1 <= item["level"] <= 5
            assert item["category"] in ("speech", "face", "cognitive", "mood")


def test_variants_dictionary() -> None:
    table = load_seed("variants_uz")
    assert len(table) >= 50
    assert table["kartishka"] == "kartoshka"
    assert "avtomobil" not in table  # semantic synonyms belong to expected.answers, not here
