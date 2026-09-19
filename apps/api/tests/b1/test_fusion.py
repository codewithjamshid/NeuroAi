"""PatientState fusion (TZ §5.4 simplified) — pure unit tests."""

from app.modules.state.fusion import FusionInputs, face_aggregates, fuse, text_valence


def test_no_inputs_is_neutral_unknown() -> None:
    state = fuse(FusionInputs(text="salom"))
    assert (state.engagement, state.mood, state.mood_conf, state.distress) == (
        "medium",
        "unknown",
        0.0,
        False,
    )
    assert state.fatigue == 0.0 and state.explain == []


def test_face_batch_drives_engagement_and_fatigue() -> None:
    batch = [
        {
            "ts": 1,
            "attention": 0.9,
            "fatigue_proxy": 0.8,
            "expr_hint": {"label": "happy", "conf": 0.7},
        },
        {"ts": 2, "attention": 0.85, "fatigue_proxy": 0.7},
        {"ts": 3, "face_present": False, "attention": 0.0},
    ]
    agg = face_aggregates(batch)
    assert agg["present"] == 2 and round(agg["attention"], 3) == 0.875
    assert agg["expr_hint"] == {"label": "happy", "conf": 0.7}
    state = fuse(FusionInputs(face_batch=batch, latency_ms=1000))
    assert state.engagement == "high"
    assert state.fatigue > 0.4 and any("charchoq" in e for e in state.explain)
    assert state.mood == "positive" and any("tabassum" in e for e in state.explain)

    low = fuse(FusionInputs(face_batch=[{"ts": 1, "attention": 0.3}]))
    assert low.engagement == "low"


def test_mood_sources_and_confidence() -> None:
    sad = fuse(FusionInputs(mood_self=1))
    assert sad.mood == "negative" and sad.mood_conf == 0.5
    mixed = fuse(FusionInputs(mood_self=5, voice={"label": "sad", "valence": 0.1, "arousal": 0.5}))
    assert mixed.inputs["voice"]["valence_signed"] == -0.8
    assert mixed.mood_conf < 0.5  # disagreement lowers confidence
    assert text_valence("bugun juda yaxshi, rahmat") == 0.5
    assert text_valence("xafaman, yomon") == -0.5
    assert text_valence("non") is None


def test_distress_from_keyword_voice_or_grimace() -> None:
    assert fuse(FusionInputs(keyword_distress=True)).distress is True
    voice = {"label": "angry", "arousal": 0.9, "valence": 0.1}
    assert fuse(FusionInputs(voice=voice)).distress is True
    face = [{"ts": 1, "expr_hint": {"label": "grimace", "conf": 0.6}}]
    assert fuse(FusionInputs(face_batch=face)).distress is True
    calm = fuse(FusionInputs(stt_confidence=0.3, latency_ms=15000))
    assert calm.distress is False and calm.engagement == "low"
    assert any("ishonchi past" in e for e in calm.explain)
