"""Interpreter: guess (LLM / low-conf board / alias fallback), confirm, board, history."""

from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient

from app.ai.providers.llm.mock import MockLLM
from app.ai.providers.stt.mock import MockSTT
from app.modules.interpreter import service
from app.modules.interpreter.schemas import Candidate
from interpreter.conftest import API, FailingLLM, silence_wav

pytestmark = pytest.mark.usefixtures("seeded", "chains")

VALID_KEYS = {i["key"] for i in service.needs_items()}


async def _guess(client: AsyncClient, actors: dict[str, Any], **form: Any) -> dict[str, Any]:
    files = {"audio": ("a.wav", form.pop("audio"), "audio/wav")} if "audio" in form else None
    resp = await client.post(
        f"{API}/interpreter/guess",
        data={"patient_id": actors["patient_id"], **form},
        files=files,
        headers=actors["patient"],
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_guess_text_three_valid_candidates(client: AsyncClient, actors: dict) -> None:
    body = await _guess(client, actors, text="su… suv")
    assert body["raw_transcript"] == "su… suv" and body["confidence"] == 1.0
    assert body["board_suggested"] is False and body["session_id"]
    assert len(body["candidates"]) == 3
    assert all(c["key"] in VALID_KEYS for c in body["candidates"])
    assert body["candidates"][0]["key"] == "water" and body["candidates"][0]["emoji"] == "💧"
    # same session reused when passed back
    again = await _guess(client, actors, text="suv", session_id=body["session_id"])
    assert again["session_id"] == body["session_id"]


async def test_guess_repairs_unknown_llm_keys(
    client: AsyncClient, actors: dict, chains: Callable[..., Any]
) -> None:
    chains(
        llm=MockLLM(
            overrides={
                "candidates": [
                    {"key": "bogus", "label": "Anor", "p": 0.5},
                    {"key": "tea", "label": "x", "p": 0.3},
                    {"key": "tea", "label": "x", "p": 0.1},
                ]
            }
        )
    )
    body = await _guess(client, actors, text="anor")
    keys = [c["key"] for c in body["candidates"]]
    assert keys[0] == "other" and body["candidates"][0]["label"] == "Anor"
    assert keys[1] == "tea" and body["candidates"][1]["label"] == "Choy"
    assert len(keys) == 3 and keys[2] in VALID_KEYS  # padded from frequent/defaults


async def test_low_confidence_audio_suggests_board(
    client: AsyncClient, actors: dict, chains: Callable[..., Any]
) -> None:
    chains(stt=MockSTT(text="", confidence=0.1))
    body = await _guess(client, actors, audio=silence_wav(0.2))
    assert body["board_suggested"] is True and body["raw_transcript"] == ""
    assert [c["key"] for c in body["candidates"]] == ["water", "food", "toilet"]


async def test_alias_fallback_when_llm_unavailable(
    client: AsyncClient, actors: dict, chains: Callable[..., Any]
) -> None:
    chains(llm=FailingLLM())
    body = await _guess(client, actors, text="cho choy ichmoqchiman")
    keys = [c["key"] for c in body["candidates"]]
    assert keys[0] == "tea" and len(keys) == 3 and len(set(keys)) == 3
    assert all(k in VALID_KEYS for k in keys)
    assert sum(c["p"] for c in body["candidates"]) <= 1.0


def test_alias_candidates_prefix_and_fuzzy() -> None:
    vocab = {i["key"]: i for i in service.needs_items()}
    keys = [c.key for c in service.alias_candidates(vocab, "su", {})]
    assert keys[0] in ("water", "sleep") and len(keys) == 3
    keys = [c.key for c in service.alias_candidates(vocab, "hojat", {"food": 5})]
    assert keys[0] == "toilet"


def test_repair_candidates_exactly_three() -> None:
    vocab = {i["key"]: i for i in service.needs_items()}
    fixed = service.repair_candidates([Candidate(key="water", label="Suv", p=1)], vocab, {})
    assert [c.key for c in fixed] == ["water", "food", "toilet"]
    fixed = service.repair_candidates(
        [Candidate(key=k, label=k, p=0.2) for k in ("a", "b", "c", "d", "water")], vocab, {}
    )
    assert len(fixed) == 3 and all(c.key == "other" for c in fixed)


async def test_confirm_updates_interpretation_and_speaks(client: AsyncClient, actors: dict) -> None:
    body = await _guess(client, actors, text="suv")
    resp = await client.post(
        f"{API}/interpreter/confirm",
        json={"interpretation_id": body["interpretation_id"], "candidate_key": "water"},
        headers=actors["caregiver"],
    )
    assert resp.status_code == 200, resp.text
    out = resp.json()
    assert out["spoken_text"] == "Men suv ichmoqchiman."
    assert out["tts_url"].startswith("/api/v1/media/tts/") and out["tts_url"].endswith(".wav")
    assert out["family_note"] and out["follow_up"] == "none" and out["chosen"] == "water"

    rows = await client.get(
        f"{API}/patients/{actors['patient_id']}/interpretations?limit=5",
        headers=actors["clinician"],
    )
    assert rows.status_code == 200
    first = rows.json()[0]
    assert first["id"] == body["interpretation_id"]
    assert first["chosen"] == "water" and first["spoken_text"] == "Men suv ichmoqchiman."
    assert first["confirmed_by"] == "caregiver" and first["family_note"] == out["family_note"]
    assert set(first) >= {"raw_transcript", "created_at"}


async def test_confirm_pain_custom_and_person(client: AsyncClient, actors: dict) -> None:
    body = await _guess(client, actors, text="og'riq")
    iid = body["interpretation_id"]
    pain = await client.post(
        f"{API}/interpreter/confirm",
        json={"interpretation_id": iid, "candidate_key": "pain"},
        headers=actors["patient"],
    )
    assert pain.json()["follow_up"] == "body_map"
    body_part = await client.post(
        f"{API}/interpreter/confirm",
        json={"interpretation_id": iid, "candidate_key": "body:head"},
        headers=actors["patient"],
    )
    assert body_part.json()["spoken_text"] == "Boshim og'riyapti."
    custom = await client.post(
        f"{API}/interpreter/confirm",
        json={"interpretation_id": iid, "custom_text": "Radioni yoqing"},
        headers=actors["patient"],
    )
    out = custom.json()
    assert out["chosen"] == "other" and out["spoken_text"] == "Radioni yoqing"
    assert "Radioni yoqing" in out["family_note"]
    person = await client.post(
        f"{API}/interpreter/confirm",
        json={"interpretation_id": iid, "candidate_key": "person:nilufar"},
        headers=actors["patient"],
    )
    assert person.json()["spoken_text"] == "Nilufarni chaqiring."
    missing = await client.post(
        f"{API}/interpreter/confirm", json={"interpretation_id": iid}, headers=actors["patient"]
    )
    assert missing.status_code == 400 and missing.json()["error"]["code"] == "input_required"


async def test_board_ordering_persons_and_body_map(client: AsyncClient, actors: dict) -> None:
    pid = actors["patient_id"]
    for key in ("tea", "tea", "toilet"):
        body = await _guess(client, actors, text="x")
        await client.post(
            f"{API}/interpreter/confirm",
            json={"interpretation_id": body["interpretation_id"], "candidate_key": key},
            headers=actors["patient"],
        )
    resp = await client.get(
        f"{API}/interpreter/board?patient_id={pid}", headers=actors["caregiver"]
    )
    assert resp.status_code == 200, resp.text
    board = resp.json()
    keys = [i["key"] for i in board["items"]]
    assert keys[:2] == ["tea", "toilet"] and keys[2] == "water"  # frequency, then seed order
    persons = [i for i in board["items"] if i["key"].startswith("person:")]
    assert {p["label"] for p in persons} == {"Nilufar", "Sardor", "Hurmat"}
    assert persons[0]["group"] == "oila" and persons[0]["emoji"] == "👤"
    assert [b["key"] for b in board["body_map"]][:3] == ["head", "chest", "belly"]
    assert set(board["items"][0]) >= {"key", "label", "emoji", "group"}


async def test_guess_requires_input_and_access(client: AsyncClient, actors: dict) -> None:
    resp = await client.post(
        f"{API}/interpreter/guess",
        data={"patient_id": actors["patient_id"]},
        headers=actors["patient"],
    )
    assert resp.status_code == 400 and resp.json()["error"]["code"] == "input_required"
    other = await client.get(
        f"{API}/interpreter/board?patient_id=00000000-0000-0000-0000-000000000001",
        headers=actors["patient"],
    )
    assert other.status_code == 404
