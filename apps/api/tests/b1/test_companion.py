"""Companion turn: text / pictogram / audio inputs, candidates, confirm, 503 on no LLM."""

import uuid
from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from b1.conftest import API, start_session

pytestmark = pytest.mark.usefixtures("seeded", "fake_telegram")

RESPONSE_KEYS = {
    "patient_message",
    "ai_message",
    "needs_confirmation",
    "candidates",
    "state",
    "risk",
    "suggested_action",
}


async def _messages(session_id: str) -> list[Any]:
    from app.db.session import get_sessionmaker
    from app.modules.sessions.models import Message

    async with get_sessionmaker()() as db:
        stmt = (
            select(Message)
            .where(Message.session_id == uuid.UUID(session_id))
            .order_by(Message.created_at, Message.id)
        )
        return list((await db.scalars(stmt)).all())


async def test_text_message_shape_persistence_and_state(
    client: AsyncClient, actors: dict[str, Any], mock_chains: Any
) -> None:
    sid = await start_session(client, actors)
    resp = await client.post(
        f"{API}/sessions/{sid}/messages",
        data={"text": "Salom, bugun bog'imda gullarni sug'ordim", "latency_ms": "1500"},
        headers=actors["patient"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert RESPONSE_KEYS <= set(body)
    assert body["patient_message"] == {
        "text": "Salom, bugun bog'imda gullarni sug'ordim",
        "stt_confidence": None,
        "provider": None,
    }
    assert body["ai_message"]["text"].startswith("Salom!")
    assert body["ai_message"]["tts_url"].startswith("/api/v1/media/tts/")
    assert body["ai_message"]["tts_provider"] == "mock"
    assert body["risk"] == {"level": "none", "category": "none", "evidence": ""}
    assert body["suggested_action"] == "none"
    assert body["state"]["engagement"] == "medium" and body["state"]["distress"] is False
    assert body["needs_confirmation"] is False and body["candidates"] == []

    msgs = await _messages(sid)
    assert [(m.role, m.modality) for m in msgs] == [("patient", "text"), ("ai", "text")]
    assert msgs[1].llm_meta["provider"] == "mock"
    assert msgs[1].llm_meta["risk"]["level"] == "none"

    state = await client.get(f"{API}/sessions/{sid}/state", headers=actors["clinician"])
    assert state.status_code == 200
    assert state.json()["ts"] is not None and state.json()["inputs"]["latency_ms"] == 1500

    transcript = await client.get(f"{API}/sessions/{sid}/transcript", headers=actors["caregiver"])
    assert [m["role"] for m in transcript.json()["messages"]] == ["patient", "ai"]


async def test_pictogram_message_uses_needs_label(
    client: AsyncClient, actors: dict[str, Any], mock_chains: Any
) -> None:
    sid = await start_session(client, actors)
    resp = await client.post(
        f"{API}/sessions/{sid}/messages",
        data={"pictogram_key": "water"},
        headers=actors["patient"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["patient_message"]["text"] == "Suv"
    msgs = await _messages(sid)
    assert msgs[0].modality == "pictogram" and msgs[0].text == "Suv"

    bad = await client.post(
        f"{API}/sessions/{sid}/messages",
        data={"pictogram_key": "nope"},
        headers=actors["patient"],
    )
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "pictogram_unknown"

    empty = await client.post(f"{API}/sessions/{sid}/messages", data={}, headers=actors["patient"])
    assert empty.status_code == 400 and empty.json()["error"]["code"] == "empty_input"


async def test_candidates_pass_through_and_confirm(
    client: AsyncClient, actors: dict[str, Any], chains_factory: Callable[..., Any]
) -> None:
    chains_factory(
        {
            "needs_confirmation": True,
            "candidates": [
                {"key": "water", "label": "", "p": 0.6},
                {"key": "pain", "label": "Og'riq", "emoji": "🤕", "p": 0.3},
                {"key": "custom", "label": "Boshqa", "p": 0.1},
            ],
        }
    )
    sid = await start_session(client, actors)
    resp = await client.post(
        f"{API}/sessions/{sid}/messages", data={"text": "s… su…"}, headers=actors["patient"]
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["needs_confirmation"] is True
    assert [c["key"] for c in body["candidates"]] == ["water", "pain", "custom"]
    assert body["candidates"][0]["label"] == "Suv" and body["candidates"][0]["emoji"] == "💧"
    assert body["candidates"][2]["label"] == "Boshqa"

    chains_factory()  # confirmation turn answers normally
    confirm = await client.post(
        f"{API}/sessions/{sid}/confirm",
        json={"candidate_key": "water"},
        headers=actors["patient"],
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["patient_message"]["text"] == "Suv"
    assert confirm.json()["needs_confirmation"] is False
    roles = [(m.role, m.modality, m.text) for m in await _messages(sid)]
    assert roles[2] == ("system", "text", "tasdiqlandi: Suv")
    assert roles[3] == ("patient", "pictogram", "Suv") and roles[4][0] == "ai"


async def test_llm_unavailable_is_503(
    client: AsyncClient, actors: dict[str, Any], chains_factory: Callable[..., Any]
) -> None:
    chains_factory(llm_fail=True)
    sid = await start_session(client, actors)
    resp = await client.post(
        f"{API}/sessions/{sid}/messages", data={"text": "salom"}, headers=actors["patient"]
    )
    assert resp.status_code == 503
    assert resp.json() == {
        "error": {"code": "llm_unavailable", "message": "Eshitolmadim, matn bilan yozing"}
    }
    # the patient message + state were still persisted before the LLM step
    assert [m.role for m in await _messages(sid)] == ["patient"]


async def test_audio_message_runs_stt_and_saves_wav(
    client: AsyncClient, actors: dict[str, Any], chains_factory: Callable[..., Any]
) -> None:
    from app.ai.audio import ffmpeg_path
    from app.ai.worker.mock import silence_wav
    from app.core.config import get_settings

    if not ffmpeg_path():
        pytest.skip("ffmpeg not available")
    chains_factory(stt_text="bog'imda gullar", stt_confidence=0.7)
    sid = await start_session(client, actors)
    face_batch = '[{"ts": 1.0, "attention": 0.95, "fatigue_proxy": 0.1}]'
    resp = await client.post(
        f"{API}/sessions/{sid}/messages",
        files={"audio": ("a.wav", silence_wav(2.0), "audio/wav")},
        data={"face_batch": face_batch, "latency_ms": "900"},
        headers=actors["patient"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["patient_message"] == {
        "text": "bog'imda gullar",
        "stt_confidence": 0.7,
        "provider": "mock",
    }
    assert body["state"]["engagement"] == "high"
    msg = (await _messages(sid))[0]
    assert msg.modality == "voice" and msg.stt_provider == "mock"
    assert msg.audio_path == f"audio/{sid}/{msg.id}.wav"
    assert (get_settings().media_dir / msg.audio_path).stat().st_size > 44

    forbidden = await client.post(
        f"{API}/sessions/{sid}/messages",
        files={"audio": ("a.webm", b"not audio at all", "audio/webm")},
        headers=actors["patient"],
    )
    assert forbidden.status_code == 400
    assert forbidden.json()["error"]["code"] == "audio_invalid"
