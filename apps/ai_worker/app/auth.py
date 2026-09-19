"""X-Worker-Key header check (TZ §4.7). /health stays public."""

import secrets
from typing import Annotated

from fastapi import Depends, Header

from app.config import Settings, get_settings
from app.errors import WorkerError


def require_worker_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_worker_key: Annotated[str | None, Header(alias="X-Worker-Key")] = None,
) -> None:
    expected = settings.worker_key
    if not expected:
        raise WorkerError(401, "unauthorized", "WORKER_KEY is not configured on the worker")
    if x_worker_key is None or not secrets.compare_digest(x_worker_key.encode(), expected.encode()):
        raise WorkerError(401, "unauthorized", "missing or invalid X-Worker-Key header")
