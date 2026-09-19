"""Aggregates module routers under /api/v1 (mounted in app.main).

Auto-discovery: every package `app.modules.<name>` that has a `router.py` exposing `router`
is included — modules never edit this file (parallel work, DEMO_SCOPE.md). Order is alphabetical;
prefixes/tags belong to each module's APIRouter.
"""

import importlib
import logging
import pkgutil

from fastapi import APIRouter

import app.modules as modules_pkg

log = logging.getLogger("neuroai.router")

router = APIRouter()

for info in sorted(pkgutil.iter_modules(modules_pkg.__path__), key=lambda i: i.name):
    if not info.ispkg:
        continue
    try:
        mod = importlib.import_module(f"app.modules.{info.name}.router")
    except ModuleNotFoundError as exc:
        if exc.name == f"app.modules.{info.name}.router":
            continue  # module without an HTTP surface (e.g. safety keywords, scoring)
        raise
    sub = getattr(mod, "router", None)
    if sub is None:
        continue
    router.include_router(sub)
    log.debug("router included", extra={"module": info.name})
