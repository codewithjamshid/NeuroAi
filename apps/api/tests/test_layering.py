"""Layering guards (CLAUDE.md, TZ §9.3): routers never reach into app.ai; app.ai has no web deps."""

import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
IMPORT_RE = r"^\s*(?:from|import)\s+{}"


def _imports(path: Path, module: str) -> list[str]:
    return re.findall(IMPORT_RE.format(re.escape(module)), path.read_text(), flags=re.MULTILINE)


def test_module_routers_do_not_import_ai_layer() -> None:
    routers = list(APP_DIR.glob("modules/*/router.py"))
    assert routers
    for router in routers:
        assert not _imports(router, "app.ai"), router


def test_ai_layer_does_not_import_fastapi() -> None:
    for path in APP_DIR.glob("ai/**/*.py"):
        assert not _imports(path, "fastapi"), path
