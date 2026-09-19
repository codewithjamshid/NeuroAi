"""FastAPI dependencies shared by module routers.

Routers import from here (plus their own service/schemas), never from `app.ai.*`; the AI layer
stays free of web-framework imports (CLAUDE.md, TZ §9.3).
"""

from typing import Annotated

from fastapi import Depends, Request

from app.ai.worker.client import WorkerClientProtocol
from app.core.config import Settings, get_settings


def worker_client_dep(request: Request) -> WorkerClientProtocol:
    """The app-wide worker client created in `create_app()` (`app.state.worker_client`)."""
    return request.app.state.worker_client


SettingsDep = Annotated[Settings, Depends(get_settings)]
WorkerDep = Annotated[WorkerClientProtocol, Depends(worker_client_dep)]
