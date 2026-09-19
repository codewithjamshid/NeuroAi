"""Audio utils: webm/opus → 16 kHz wav (static-ffmpeg), wav helpers, TTS cache (TZ §4.3, §4.8)."""

import asyncio
import hashlib
import io
import logging
import os
import shutil
import tempfile
import threading
import uuid
import wave
from pathlib import Path
from typing import Any

import static_ffmpeg

from app.ai.providers.base import ProviderError, ProviderUnavailable
from app.ai.worker.mock import silence_wav
from app.core.config import get_settings

__all__ = [
    "AudioConversionError",
    "ffmpeg_path",
    "run_ffmpeg",
    "silence_wav",
    "synthesize_cached",
    "tts_cache_key",
    "tts_cache_path",
    "tts_url",
    "wav_duration_s",
    "webm_to_wav16k",
]

log = logging.getLogger("neuroai.ai.audio")

TTS_URL_PREFIX = "/api/v1/media/tts"  # mounted in app.main (also /media/tts)
FFMPEG_TIMEOUT_S = 20.0

_ffmpeg_lock = threading.Lock()
_ffmpeg_path: str | None = None


class AudioConversionError(ProviderError):
    pass


def ffmpeg_path() -> str | None:
    """ffmpeg executable (static-ffmpeg's bundled binary, else the system one); None if absent."""
    global _ffmpeg_path
    if _ffmpeg_path:
        return _ffmpeg_path
    with _ffmpeg_lock:
        if _ffmpeg_path:
            return _ffmpeg_path
        try:
            static_ffmpeg.add_paths(weak=True)  # once; keeps a system ffmpeg if already on PATH
        except Exception as exc:
            log.warning("static_ffmpeg unavailable", extra={"error": type(exc).__name__})
        _ffmpeg_path = shutil.which("ffmpeg")
    return _ffmpeg_path


async def run_ffmpeg(args: list[str], stdin: bytes | None = None) -> bytes:
    exe = ffmpeg_path()
    if not exe:
        raise AudioConversionError("ffmpeg not available")
    proc = await asyncio.create_subprocess_exec(
        exe,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        *args,
        stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(stdin), timeout=FFMPEG_TIMEOUT_S)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise AudioConversionError("ffmpeg timeout") from None
    if proc.returncode != 0:
        detail = err.decode(errors="replace").strip()[-300:]
        raise AudioConversionError(detail or f"ffmpeg exit {proc.returncode}")
    return out


async def webm_to_wav16k(data: bytes) -> bytes:
    """MediaRecorder webm/opus (or any ffmpeg-readable audio) → 16 kHz mono 16-bit PCM wav."""
    if not data:
        raise AudioConversionError("empty audio")
    with tempfile.TemporaryDirectory(prefix="neuroai-audio-") as tmp:
        src, dst = Path(tmp) / "in.webm", Path(tmp) / "out.wav"
        src.write_bytes(data)
        await run_ffmpeg(
            ["-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dst)]
        )
        return dst.read_bytes()


def wav_duration_s(wav: bytes) -> float:
    try:
        with wave.open(io.BytesIO(wav)) as w:
            rate = w.getframerate()
            return w.getnframes() / rate if rate else 0.0
    except (wave.Error, EOFError):
        return 0.0


# --- TTS cache: MEDIA_DIR/tts/<sha1(provider + text)>.wav ---------------------------------


def tts_cache_key(text: str, provider: str) -> str:
    return hashlib.sha1(f"{provider}\x00{text.strip()}".encode()).hexdigest()


def tts_cache_path(text: str, provider: str, media_dir: Path | None = None) -> Path:
    base = media_dir if media_dir is not None else get_settings().media_dir
    return Path(base) / "tts" / f"{tts_cache_key(text, provider)}.wav"


def tts_url(path: Path) -> str:
    return f"{TTS_URL_PREFIX}/{path.name}"


async def synthesize_cached(
    chains: Any, text: str, speed: float | None = None, *, media_dir: Path | None = None
) -> tuple[str | None, str]:
    """→ ("/api/v1/media/tts/<sha1>.wav", provider) or (None, "browser") when no audio."""
    settings = get_settings()
    speed = settings.tts_speed if speed is None else speed
    base = media_dir if media_dir is not None else settings.media_dir
    text = text.strip()
    if not text:
        return None, "browser"
    for provider in chains.tts.providers:  # cache hit for any real provider, no call made
        name = getattr(provider, "name", "")
        if name == "browser" or not getattr(provider, "configured", True):
            continue
        path = tts_cache_path(text, name, base)
        if path.is_file():
            return tts_url(path), name
    try:
        result = await chains.tts.call("synthesize", text, speed=speed)
    except ProviderUnavailable:
        log.warning("tts: all providers failed, browser fallback")
        return None, "browser"
    if result.browser or not result.audio_wav:
        return None, result.provider
    path = tts_cache_path(text, result.provider, base)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.stem}.{uuid.uuid4().hex}.tmp")
    tmp.write_bytes(result.audio_wav)
    os.replace(tmp, path)
    return tts_url(path), result.provider
