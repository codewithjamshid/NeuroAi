"""Startup/shutdown hooks modules register at import time (app.main runs them in lifespan).

Modules are imported by the /api/v1 router auto-discovery before the lifespan starts, so
`register_startup(fn)` at module level is enough — no edits to app/main.py needed.
Hooks receive the FastAPI app; async or sync callables are accepted.
"""

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

log = logging.getLogger("neuroai.hooks")

Hook = Callable[[Any], Awaitable[None] | None]
_STARTUP: list[Hook] = []
_SHUTDOWN: list[Hook] = []


def register_startup(fn: Hook) -> Hook:
    _STARTUP.append(fn)
    return fn


def register_shutdown(fn: Hook) -> Hook:
    _SHUTDOWN.append(fn)
    return fn


async def _run(hooks: list[Hook], app: Any, stage: str) -> None:
    for fn in hooks:
        try:
            result = fn(app)
            if inspect.isawaitable(result):
                await result
        except Exception:  # a broken hook must not take the API down
            log.exception("%s hook failed: %s", stage, getattr(fn, "__qualname__", fn))


async def run_startup(app: Any) -> None:
    await _run(_STARTUP, app, "startup")


async def run_shutdown(app: Any) -> None:
    await _run(list(reversed(_SHUTDOWN)), app, "shutdown")
    # give cancelled background tasks a tick to unwind
    await asyncio.sleep(0)
