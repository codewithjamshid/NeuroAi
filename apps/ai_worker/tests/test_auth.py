import pytest
from httpx import AsyncClient

from app.config import get_settings


def _error(r) -> dict:
    body = r.json()
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}
    return body["error"]


async def test_stt_without_key_is_401(client: AsyncClient, wav_bytes: bytes) -> None:
    r = await client.post("/stt", files={"audio": ("a.wav", wav_bytes, "audio/wav")})
    assert r.status_code == 401
    assert _error(r)["code"] == "unauthorized"


async def test_stt_with_wrong_key_is_401(client: AsyncClient, wav_bytes: bytes) -> None:
    r = await client.post(
        "/stt",
        headers={"X-Worker-Key": "nope"},
        files={"audio": ("a.wav", wav_bytes, "audio/wav")},
    )
    assert r.status_code == 401


async def test_stt_with_key_is_503_model_not_loaded(
    client: AsyncClient, auth: dict[str, str], wav_bytes: bytes
) -> None:
    r = await client.post(
        "/stt",
        headers=auth,
        params={"lang": "uz", "initial_prompt": "suv"},
        files={"audio": ("a.wav", wav_bytes, "audio/wav")},
    )
    assert r.status_code == 503
    err = _error(r)
    assert err["code"] == "model_not_loaded"
    assert "stt" in err["message"] and "docs/AI_WORKER_TZ.md" in err["message"]


async def test_stt_with_key_but_no_file_is_422(client: AsyncClient, auth: dict[str, str]) -> None:
    r = await client.post("/stt", headers=auth)
    assert r.status_code == 422
    assert _error(r)["code"] == "validation_error"


@pytest.mark.parametrize(
    ("path", "kwargs", "model"),
    [
        ("/tts", {"json": {"text": "Salom", "speed": 0.85, "style": "neutral"}}, "tts"),
        ("/medllm/summarize", {"json": {"text": "epikriz", "task": "discharge_summary"}}, "medllm"),
    ],
)
async def test_json_endpoints_503_when_not_loaded(
    client: AsyncClient, auth: dict[str, str], path: str, kwargs: dict, model: str
) -> None:
    assert (await client.post(path, **kwargs)).status_code == 401
    r = await client.post(path, headers=auth, **kwargs)
    assert r.status_code == 503
    assert _error(r)["message"].startswith(f"{model} model not loaded")


async def test_voice_emotion_503_when_not_loaded(
    client: AsyncClient, auth: dict[str, str], wav_bytes: bytes
) -> None:
    files = {"audio": ("a.wav", wav_bytes, "audio/wav")}
    assert (await client.post("/voice-emotion", files=files)).status_code == 401
    r = await client.post("/voice-emotion", headers=auth, files=files)
    assert r.status_code == 503
    assert _error(r)["code"] == "model_not_loaded"


async def test_empty_worker_key_rejects_everything(
    monkeypatch: pytest.MonkeyPatch, client: AsyncClient, wav_bytes: bytes
) -> None:
    monkeypatch.setenv("WORKER_KEY", "")
    get_settings.cache_clear()
    r = await client.post(
        "/stt", headers={"X-Worker-Key": ""}, files={"audio": ("a.wav", wav_bytes, "audio/wav")}
    )
    assert r.status_code == 401
    assert (await client.get("/health")).status_code == 200
