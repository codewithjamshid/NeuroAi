"""Prompt files → text. `render()` fills `{key}` placeholders via str.replace (no format())."""

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
PROMPT_NAMES: tuple[str, ...] = (
    "companion",
    "interpreter",
    "coach",
    "risk_classifier",
    "session_summary",
    "weekly_report",
    "caregiver_tips",
)


@lru_cache
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"prompt not found: {name}")
    return path.read_text(encoding="utf-8").strip()


def render(name: str, **vars: object) -> str:
    """Replace each `{key}` with str(value); unknown placeholders are left untouched."""
    text = load_prompt(name)
    for key, value in vars.items():
        text = text.replace("{" + key + "}", str(value))
    return text


def list_prompts() -> list[str]:
    return sorted(p.stem for p in PROMPTS_DIR.glob("*.md") if p.stem != "README")
