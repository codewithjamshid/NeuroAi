"""POST /api/v1/tts: mock chain → cached url; cache hit skips the provider; blank → 400; 401."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient

from app.ai.chains import Chains
from app.ai.providers.tts.mock import MockTTS
from tts.conftest import API

pytestmark = pytest.mark.usefixtures("seeded", "chains")

TEXT = "Tabassum qiling va 3 soniya ushlab turing."


async def test_mock_chain_returns_cached_wav_url(
    client: AsyncClient, actors: dict[str, Any], media_dir: Path
) -> None:
    resp = await client.post(f"{API}/tts", json={"text": TEXT}, headers=actors["patient"])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["tts_url"].startswith("/api/v1/media/tts/") and body["tts_url"].endswith(".wav")
    wav = media_dir / "tts" / body["tts_url"].rsplit("/", 1)[-1]
    assert wav.is_file() and wav.read_bytes()[:4] == b"RIFF"


async def test_cache_hit_skips_provider(
    client: AsyncClient, actors: dict[str, Any], chains: Callable[..., Chains]
) -> None:
    first = await client.post(f"{API}/tts", json={"text": TEXT}, headers=actors["patient"])
    assert first.status_code == 200, first.text
    chains(tts=MockTTS(fail=True))  # would fail if called — the cache must answer instead
    again = await client.post(
        f"{API}/tts", json={"text": f"  {TEXT} ", "speed": 1.0}, headers=actors["clinician"]
    )
    assert again.status_code == 200, again.text
    assert again.json() == first.json()


async def test_all_providers_down_yields_browser(
    client: AsyncClient, actors: dict[str, Any], chains: Callable[..., Chains]
) -> None:
    chains(tts=MockTTS(fail=True))
    resp = await client.post(f"{API}/tts", json={"text": "Salom"}, headers=actors["caregiver"])
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"tts_url": None, "provider": "browser"}


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
async def test_blank_text_is_400_empty_input(
    client: AsyncClient, actors: dict[str, Any], text: str
) -> None:
    resp = await client.post(f"{API}/tts", json={"text": text}, headers=actors["patient"])
    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["code"] == "empty_input"


async def test_too_long_text_is_422(client: AsyncClient, actors: dict[str, Any]) -> None:
    resp = await client.post(f"{API}/tts", json={"text": "a" * 601}, headers=actors["patient"])
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "validation_error"


async def test_unauthenticated_is_401(client: AsyncClient) -> None:
    resp = await client.post(f"{API}/tts", json={"text": TEXT})
    assert resp.status_code == 401, resp.text
    assert resp.json()["error"]["code"] == "unauthorized"
