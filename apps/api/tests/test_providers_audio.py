"""app.ai.audio: ffmpeg conversion (static-ffmpeg), wav helpers, TTS cache + synthesize_cached."""

import io
import wave
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.ai.audio import (
    AudioConversionError,
    ffmpeg_path,
    run_ffmpeg,
    silence_wav,
    synthesize_cached,
    tts_cache_key,
    tts_cache_path,
    tts_url,
    wav_duration_s,
    webm_to_wav16k,
)
from app.ai.chains import Chains, FallbackChain, build_chains, recent_calls, reset_chains
from app.ai.providers.tts.base import TTSProvider
from app.ai.providers.tts.browser import BrowserTTS
from app.ai.providers.tts.mock import MockTTS
from app.core.config import Settings, get_settings

needs_ffmpeg = pytest.mark.skipif(ffmpeg_path() is None, reason="ffmpeg not available")


@pytest.fixture(autouse=True)
def _reset() -> Iterator[None]:
    reset_chains()
    yield
    reset_chains()


@needs_ffmpeg
async def test_webm_to_wav16k_converts_opus(tmp_path: Path) -> None:
    webm = tmp_path / "in.webm"
    await run_ffmpeg(
        ["-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "0.5", "-c:a", "libopus"]
        + [str(webm)]
    )
    wav = await webm_to_wav16k(webm.read_bytes())
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    with wave.open(io.BytesIO(wav)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 16_000)
    assert 0.4 <= wav_duration_s(wav) <= 0.6


@needs_ffmpeg
async def test_webm_to_wav16k_rejects_garbage() -> None:
    with pytest.raises(AudioConversionError):
        await webm_to_wav16k(b"this is not audio")


async def test_webm_to_wav16k_rejects_empty() -> None:
    with pytest.raises(AudioConversionError):
        await webm_to_wav16k(b"")


def test_wav_duration_s() -> None:
    assert wav_duration_s(silence_wav(0.5)) == 0.5
    assert wav_duration_s(b"garbage") == 0.0


def test_tts_cache_path_stable(tmp_path: Path) -> None:
    p1 = tts_cache_path("Salom, Bobur aka!", "worker", tmp_path)
    p2 = tts_cache_path("  Salom, Bobur aka!  ", "worker", tmp_path)
    assert p1 == p2
    assert p1.parent == tmp_path / "tts" and p1.suffix == ".wav" and len(p1.stem) == 40
    assert p1.stem == tts_cache_key("Salom, Bobur aka!", "worker")
    assert tts_cache_path("Salom, Bobur aka!", "openai", tmp_path) != p1
    assert tts_cache_path("Boshqa matn", "worker", tmp_path) != p1
    assert tts_url(p1) == f"/api/v1/media/tts/{p1.name}"


def test_tts_cache_path_defaults_to_settings_media_dir() -> None:
    assert tts_cache_path("x", "y").parent == get_settings().media_dir / "tts"


def _chains_with_tts(*providers: TTSProvider) -> Chains:
    chains = build_chains(Settings(_env_file=None, gemini_api_key="", openai_api_key=""))
    chains.tts = FallbackChain(list(providers), timeout_s=1, task="tts")
    return chains


async def test_synthesize_cached_writes_file_then_hits_cache(tmp_path: Path) -> None:
    chains = _chains_with_tts(MockTTS(), BrowserTTS())
    url, provider = await synthesize_cached(chains, "Salom!", 0.85, media_dir=tmp_path)
    assert provider == "mock"
    assert url is not None and url.startswith("/api/v1/media/tts/") and url.endswith(".wav")
    path = tmp_path / "tts" / url.rsplit("/", 1)[1]
    assert path.is_file() and wav_duration_s(path.read_bytes()) == 1.0
    assert not list((tmp_path / "tts").glob("*.tmp"))
    calls_before = len(recent_calls())
    assert await synthesize_cached(chains, " Salom! ", 0.85, media_dir=tmp_path) == (url, "mock")
    assert len(recent_calls()) == calls_before  # served from cache: no provider call


async def test_synthesize_cached_browser_fallback(tmp_path: Path) -> None:
    chains = _chains_with_tts(MockTTS(fail=True), BrowserTTS())
    assert await synthesize_cached(chains, "Salom", media_dir=tmp_path) == (None, "browser")
    assert not (tmp_path / "tts").exists()


async def test_synthesize_cached_all_fail_and_empty_text(tmp_path: Path) -> None:
    chains = _chains_with_tts(MockTTS(fail=True))
    assert await synthesize_cached(chains, "Salom", media_dir=tmp_path) == (None, "browser")
    assert await synthesize_cached(chains, "   ", media_dir=tmp_path) == (None, "browser")


async def test_synthesize_cached_default_speed_from_settings(tmp_path: Path) -> None:
    chains = _chains_with_tts(MockTTS())
    url, provider = await synthesize_cached(chains, "Salom", media_dir=tmp_path)
    assert provider == "mock" and url is not None
