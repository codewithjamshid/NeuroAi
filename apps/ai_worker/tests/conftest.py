import io
import struct
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings

TEST_KEY = "test-worker-key"


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Deterministic settings regardless of the developer's .env files."""
    monkeypatch.setenv("WORKER_KEY", TEST_KEY)
    monkeypatch.setenv("MODELS_ENABLED", "")
    get_settings.cache_clear()
    yield {"WORKER_KEY": TEST_KEY}
    get_settings.cache_clear()


@pytest.fixture
async def client(env: dict[str, str]) -> AsyncIterator[AsyncClient]:
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def auth() -> dict[str, str]:
    return {"X-Worker-Key": TEST_KEY}


@pytest.fixture
def wav_bytes() -> bytes:
    """0.1 s of 16 kHz mono PCM16 silence with a valid RIFF header."""
    n_samples = 1600
    data = b"\x00\x00" * n_samples
    header = b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, 16000, 32000, 2, 16)
    header += b"data" + struct.pack("<I", len(data))
    return io.BytesIO(header + data).getvalue()
