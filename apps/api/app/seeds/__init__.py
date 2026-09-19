"""Seed JSON files (TZ §7.6, §7.7, Ilova C). `load_seed("exercises_uz")` → parsed JSON."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SEEDS_DIR = Path(__file__).resolve().parent


@lru_cache
def load_seed(name: str) -> Any:
    return json.loads((SEEDS_DIR / f"{name}.json").read_text(encoding="utf-8"))
