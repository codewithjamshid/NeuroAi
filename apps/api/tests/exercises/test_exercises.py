"""Exercise engine: plan, next/submit (correct, cue ladder, unclear, LLM judge), adaptive level,
face summary, skip, templates listing."""

import uuid
from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient
from interpreter.conftest import API, FailingLLM, silence_wav
from sqlalchemy import select

from app.ai.providers.llm.mock import MockLLM
from app.ai.providers.stt.mock import MockSTT
from app.modules.exercises import plan as planner
from app.modules.exercises import service
from app.modules.exercises.schemas import FaceSummary
from app.modules.exercises.scoring import score_answer

pytestmark = pytest.mark.usefixtures("seeded", "chains")


class T:
    def __init__(self, key: str, subtype: str, level: int) -> None:
        self.key, self.subtype, self.level = key, subtype, level


async def _session(client: AsyncClient, actors: dict[str, Any]) -> str:
    resp = await client.post(
        f"{API}/sessions",
        json={"patient_id": actors["patient_id"], "mode": "exercise"},
        headers=actors["patient"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _set_plan(session_id: str, keys: list[str], level: int = 1) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import Session

    async with get_sessionmaker()() as db:
        session = await db.get(Session, uuid.UUID(session_id))
        assert session is not None
        planner.save_plan(
            session,
            {"category": "speech", "level": level, "keys": keys, "index": 0, "streak_from": 0},
        )
        await db.commit()


async def _next(client: AsyncClient, actors: dict, sid: str) -> dict[str, Any]:
    resp = await client.get(f"{API}/sessions/{sid}/exercises/next", headers=actors["patient"])
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _submit(client: AsyncClient, actors: dict, attempt_id: str, **form: Any) -> dict:
    files = {"audio": ("a.wav", form.pop("audio"), "audio/wav")} if "audio" in form else None
    resp = await client.post(
        f"{API}/exercise-attempts/{attempt_id}/submit",
        data=form,
        files=files,
        headers=actors["patient"],
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _speech_level(patient_id: str) -> int:
    from app.db.session import get_sessionmaker
    from app.modules.patients.models import PatientLevel

    async with get_sessionmaker()() as db:
        stmt = select(PatientLevel.level).where(
            PatientLevel.patient_id == uuid.UUID(patient_id), PatientLevel.category == "speech"
        )
        return int(await db.scalar(stmt) or 0)


# --- plan -----------------------------------------------------------------------------------


def test_select_items_mixes_subtypes_and_prefers_level() -> None:
    templates = [
        *[T(f"naming_l1_{i}", "naming", 1) for i in range(10)],
        *[T(f"rep_l1_{i}", "repetition", 1) for i in range(3)],
        *[T(f"naming_l2_{i}", "naming", 2) for i in range(5)],
        *[T(f"comp_l2_{i}", "completion", 2) for i in range(5)],
    ]
    keys = planner.select_items(templates, ["naming", "repetition"], 1, set(), [])
    assert len(keys) == 8 and keys[:4] == ["naming_l1_0", "rep_l1_0", "naming_l1_1", "rep_l1_1"]
    assert not any(k.startswith("comp") for k in keys)
    # recent items are excluded, failed-old ones come first
    keys = planner.select_items(
        templates, ["naming"], 1, {f"naming_l1_{i}" for i in range(9)}, ["naming_l1_3"]
    )
    assert keys[0] == "naming_l1_3" and keys[1] == "naming_l1_9"
    assert keys[2] == "naming_l2_0"  # level 1 exhausted → nearest level
    # level 3 with only l1/l2 content → closest (l2) first
    keys = planner.select_items(templates, ["naming"], 3, set(), [], size=3)
    assert keys == ["naming_l2_0", "naming_l2_1", "naming_l2_2"]


async def test_plan_built_from_protocol_and_level(client: AsyncClient, actors: dict) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import ExerciseTemplate, Session

    sid = await _session(client, actors)
    first = await _next(client, actors, sid)
    assert first["progress"] == {"index": 1, "total": 8} and first["cue_level"] == 0
    tpl = first["template"]
    assert tpl["category"] == "speech" and tpl["level"] == 1 and "expected" not in tpl
    assert tpl["prompt_tts_url"].startswith("/api/v1/media/tts/")
    assert set(tpl) >= {"id", "key", "subtype", "prompt_text", "stimulus", "cues"}
    async with get_sessionmaker()() as db:
        session = await db.get(Session, uuid.UUID(sid))
        plan = planner.get_plan(session)
        assert len(plan["keys"]) == 8 and len(set(plan["keys"])) == 8 and plan["level"] == 1
        rows = (
            await db.scalars(select(ExerciseTemplate).where(ExerciseTemplate.key.in_(plan["keys"])))
        ).all()
        assert all(r.category == "speech" and r.level == 1 for r in rows)
        assert len({r.subtype for r in rows}) >= 2  # naming + repetition mix
    # idempotent: same pending attempt on reload
    assert (await _next(client, actors, sid))["attempt_id"] == first["attempt_id"]


# --- submit ---------------------------------------------------------------------------------


async def test_correct_text_answer(client: AsyncClient, actors: dict) -> None:
    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy", "naming_l1_non"])
    item = await _next(client, actors, sid)
    assert item["template"]["key"] == "naming_l1_choy" and item["template"]["stimulus"] == {
        "emoji": "🍵"
    }
    out = await _submit(client, actors, item["attempt_id"], text="choy", response_ms=1800)
    assert out["result"] == "correct" and out["score"] == 1.0
    assert out["feedback_text"] == "To'g'ri! Choy." and out["next_action"] == "next_item"
    assert out["tts_url"].endswith(".wav") and out["next_cue"] is None
    second = await _next(client, actors, sid)
    assert second["template"]["key"] == "naming_l1_non" and second["progress"]["index"] == 2
    # re-submitting a finished attempt is refused
    resp = await client.post(
        f"{API}/exercise-attempts/{item['attempt_id']}/submit",
        data={"text": "choy"},
        headers=actors["patient"],
    )
    assert resp.status_code == 409


async def test_cue_ladder_then_next_item(client: AsyncClient, actors: dict) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import ExerciseAttempt

    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy", "naming_l1_non"])
    item = await _next(client, actors, sid)
    aid = item["attempt_id"]
    r1 = await _submit(client, actors, aid, text="uy")  # incorrect, no LLM (conf 1.0)
    assert r1["result"] == "incorrect" and r1["next_action"] == "retry_with_cue"
    assert r1["next_cue"]["level"] == 1 and r1["next_cue"]["text"].startswith("Bu ichiladi")
    assert r1["next_cue"]["tts_url"].endswith(".wav")
    r2 = await _submit(client, actors, aid, text="uy")
    assert r2["next_cue"]["level"] == 2 and r2["next_cue"]["text"] == "cho…"
    r3 = await _submit(client, actors, aid, text="uy")
    assert r3["next_cue"]["level"] == 3
    assert r3["next_cue"]["text"] == "Men aytaman, siz takrorlang: choy."
    r4 = await _submit(client, actors, aid, text="uy")
    assert r4["next_action"] == "next_item" and r4["next_cue"] is None
    assert r4["result"] == "incorrect" and "keyingi safar" in r4["feedback_text"]
    async with get_sessionmaker()() as db:
        attempt = await db.get(ExerciseAttempt, uuid.UUID(aid))
        assert attempt.result == "incorrect" and attempt.cue_level == 3
        assert attempt.expected_answer == "choy" and attempt.recognized_text == "uy"
        assert len(attempt.llm_judgement["history"]) == 4 and attempt.category == "speech"
    assert (await _next(client, actors, sid))["template"]["key"] == "naming_l1_non"


async def test_correct_after_cue_keeps_cue_level(client: AsyncClient, actors: dict) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import ExerciseAttempt

    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy"])
    aid = (await _next(client, actors, sid))["attempt_id"]
    await _submit(client, actors, aid, text="uy")
    out = await _submit(client, actors, aid, text="choy")
    assert out["result"] == "correct" and out["next_action"] == "next_item"
    async with get_sessionmaker()() as db:
        attempt = await db.get(ExerciseAttempt, uuid.UUID(aid))
        assert attempt.cue_level == 1 and attempt.result == "correct"
    done = await _next(client, actors, sid)
    assert done["done"] is True
    assert done["summary"]["attempts"] == 1 and done["summary"]["independence"] == 0.0


async def test_llm_judge_partial_uses_verdict(
    client: AsyncClient, actors: dict, chains: Callable[..., Any]
) -> None:
    chains(
        llm=MockLLM(
            overrides={
                "result": "partial",
                "feedback_text": "Deyarli! Birinchi bo'g'in chiqdi.",
                "next_action": "retry_with_cue",
            }
        )
    )
    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy"])
    aid = (await _next(client, actors, sid))["attempt_id"]
    assert score_answer(["choy"], "ch", 1.0).result == "partial"
    out = await _submit(client, actors, aid, text="ch")
    assert (
        out["result"] == "partial" and out["feedback_text"] == "Deyarli! Birinchi bo'g'in chiqdi."
    )
    assert out["next_action"] == "retry_with_cue" and out["next_cue"]["level"] == 1
    # LLM down → deterministic partial feedback
    chains(llm=FailingLLM())
    out = await _submit(client, actors, aid, text="ch")
    assert out["result"] == "partial" and out["feedback_text"].startswith("Deyarli!")
    assert out["next_cue"]["level"] == 2


async def test_unclear_twice_becomes_skipped(
    client: AsyncClient, actors: dict, chains: Callable[..., Any]
) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import ExerciseAttempt

    chains(stt=MockSTT(text="", confidence=0.2))
    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy", "naming_l1_non"])
    aid = (await _next(client, actors, sid))["attempt_id"]
    r1 = await _submit(client, actors, aid, audio=silence_wav(0.2))
    assert (
        r1["result"] == "unclear" and r1["feedback_text"] == "Eshitolmadim, yana bir bor aytasizmi?"
    )
    assert r1["next_action"] == "retry_with_cue" and r1["next_cue"] is None
    r2 = await _submit(client, actors, aid, audio=silence_wav(0.2))
    assert r2["result"] == "skipped" and r2["next_action"] == "next_item"
    async with get_sessionmaker()() as db:
        attempt = await db.get(ExerciseAttempt, uuid.UUID(aid))
        assert attempt.result == "skipped" and attempt.llm_judgement["unclear"] == 2
    assert (await _next(client, actors, sid))["template"]["key"] == "naming_l1_non"


async def test_audio_stt_path_scores(client: AsyncClient, actors: dict, chains: Callable) -> None:
    chains(stt=MockSTT(text="choy", confidence=0.9))
    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy"])
    aid = (await _next(client, actors, sid))["attempt_id"]
    out = await _submit(client, actors, aid, audio=silence_wav(0.2))
    assert out["result"] == "correct" and out["recognized_text"] == "choy"


async def test_adaptive_level_up_after_three_correct(client: AsyncClient, actors: dict) -> None:
    pid = actors["patient_id"]
    assert await _speech_level(pid) == 1
    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy", "naming_l1_non", "naming_l1_suv", "naming_l1_uy"])
    for answer in ("choy", "non", "suv"):
        aid = (await _next(client, actors, sid))["attempt_id"]
        assert (await _submit(client, actors, aid, text=answer))["result"] == "correct"
    assert await _speech_level(pid) == 2
    aid = (await _next(client, actors, sid))["attempt_id"]
    await _submit(client, actors, aid, text="uy")
    assert await _speech_level(pid) == 2  # streak reset after the bump
    done = await _next(client, actors, sid)
    assert done["done"] is True and done["summary"]["accuracy"] == 1.0
    assert done["summary"]["independence"] == 1.0 and done["summary"]["attempts"] == 4


def test_face_score_formula() -> None:
    score, result = service.face_score(
        FaceSummary(reps=5, target_reps=5, mean_amplitude=0.8, fsi=0.9)
    )
    assert score == 0.92 and result == "correct"
    score, result = service.face_score(
        FaceSummary(reps=2, target_reps=5, mean_amplitude=0.5, fsi=0.5)
    )
    assert score == 0.45 and result == "partial"
    assert service.face_score(FaceSummary(reps=0, target_reps=5))[1] == "incorrect"


async def test_face_summary_submit(client: AsyncClient, actors: dict) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import ExerciseAttempt

    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy"])
    aid = (await _next(client, actors, sid))["attempt_id"]
    out = await _submit(
        client, actors, aid,
        face_summary='{"reps": 3, "target_reps": 5, "mean_amplitude": 0.6, "fsi": 0.5}',
    )  # fmt: skip
    assert out["result"] == "partial" and out["score"] == 0.58
    assert "Yana 2 ta takror" in out["feedback_text"] and "teng" in out["feedback_text"]
    assert out["next_action"] == "next_item" and out["tts_url"]
    async with get_sessionmaker()() as db:
        attempt = await db.get(ExerciseAttempt, uuid.UUID(aid))
        assert attempt.category == "face" and attempt.llm_judgement["face_summary"]["reps"] == 3
    bad = await client.post(
        f"{API}/exercise-attempts/{aid}/submit",
        data={"face_summary": "{bad"},
        headers=actors["patient"],
    )
    assert bad.status_code == 422


async def test_skip(client: AsyncClient, actors: dict) -> None:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import ExerciseAttempt

    sid = await _session(client, actors)
    await _set_plan(sid, ["naming_l1_choy", "naming_l1_non"])
    aid = (await _next(client, actors, sid))["attempt_id"]
    resp = await client.post(f"{API}/exercise-attempts/{aid}/skip", headers=actors["caregiver"])
    assert resp.status_code == 200 and resp.json() == {"ok": True}
    async with get_sessionmaker()() as db:
        assert (await db.get(ExerciseAttempt, uuid.UUID(aid))).result == "skipped"
    assert (await _next(client, actors, sid))["template"]["key"] == "naming_l1_non"


async def test_templates_listing_clinician_only(client: AsyncClient, actors: dict) -> None:
    resp = await client.get(
        f"{API}/exercise-templates?category=speech&level=2&limit=5", headers=actors["clinician"]
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 5 and all(r["level"] == 2 and r["category"] == "speech" for r in rows)
    assert set(rows[0]) >= {"id", "key", "subtype", "prompt_text", "expected", "cues"}
    forbidden = await client.get(f"{API}/exercise-templates", headers=actors["patient"])
    assert forbidden.status_code == 403
