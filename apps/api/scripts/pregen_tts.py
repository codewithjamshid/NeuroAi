"""Pre-generate (cache) TTS for static texts: exercise prompts/cues/feedback, face instructions,
safe scripts, common UI phrases (TZ §3 "TTS keshlangan prompt'lar ≤ 0.5 s").

Usage: cd apps/api && uv run python scripts/pregen_tts.py [--concurrency 3] [--limit N]
Uses the configured TTS chain (root .env, e.g. worker=Navoiy); skips texts already cached.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.audio import synthesize_cached, tts_cache_path  # noqa: E402
from app.ai.chains import get_chains  # noqa: E402
from app.ai.prompts.safe_scripts_uz import (  # noqa: E402
    fall_script,
    medication_reply,
    self_harm_script,
    stroke_signs_script,
)
from app.core.config import get_settings  # noqa: E402
from app.seeds import load_seed  # noqa: E402

UI_PHRASES = [
    "Eshitolmadim, yana bir bor aytasizmi?",
    "Bir oz dam olaylik.",
    "Salom! Sizni eshityapman.",
    "Mikrofonni bosing va gapiring. Men eshitaman.",
    "Tinch turing, yuzingizni kameraga qarating.",
    "Barakalla! Mashq tugadi.",
    "Keyingi mashq.",
]


def collect_texts() -> list[str]:
    texts: list[str] = list(UI_PHRASES)
    for item in load_seed("exercises_uz"):
        answers = item.get("expected", {}).get("answers") or []
        answer = answers[0] if answers else ""
        cues = item.get("cues") or {}
        texts.append(item["prompt_text"])
        if cues.get("semantic"):
            texts.append(cues["semantic"])
        if cues.get("phonemic"):
            texts.append(cues["phonemic"])
        if answer:
            texts.append(f"Men aytaman, siz takrorlang: {answer}.")
            texts.append(f"To'g'ri! {answer.capitalize()}.")
    for fx in load_seed("face_exercises"):
        for key in ("title", "instruction"):
            if fx.get(key):
                texts.append(fx[key])
    texts += [
        self_harm_script("Nilufar"),
        stroke_signs_script("Nilufar", "103"),
        fall_script("Nilufar"),
        medication_reply(),
        "Deyarli! Birinchi bo'g'in to'g'ri.",
        "Yana urinib ko'ring.",
    ]
    seen: set[str] = set()
    out: list[str] = []
    for t in texts:
        t = (t or "").strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    settings = get_settings()
    chains = get_chains(settings)
    provider = settings.tts_providers[0] if settings.tts_providers else "browser"
    texts = collect_texts()
    if args.limit:
        texts = texts[: args.limit]
    todo = [t for t in texts if not tts_cache_path(t, provider, settings.media_dir).exists()]
    print(f"texts: {len(texts)} | cached: {len(texts) - len(todo)} | to generate: {len(todo)}")

    sem = asyncio.Semaphore(args.concurrency)
    ok = fail = 0
    started = time.perf_counter()

    async def one(i: int, text: str) -> None:
        nonlocal ok, fail
        async with sem:
            t0 = time.perf_counter()
            url, prov = await synthesize_cached(chains, text, settings.tts_speed)
            ms = int((time.perf_counter() - t0) * 1000)
            if url:
                ok += 1
            else:
                fail += 1
            if i % 10 == 0 or not url:
                status = "OK" if url else "FAIL"
                print(f"[{i + 1}/{len(todo)}] {prov} {ms} ms {status}: {text[:50]}")

    await asyncio.gather(*(one(i, t) for i, t in enumerate(todo)))
    print(f"done: ok={ok} fail={fail} in {time.perf_counter() - started:.0f}s")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
