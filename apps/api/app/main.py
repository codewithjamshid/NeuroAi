"""FastAPI application factory. `uvicorn app.main:app`."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import APP_NAME, __version__
from app.ai.worker.client import get_worker_client
from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.errors import UnhandledErrorMiddleware, register_error_handlers
from app.core.logging import REQUEST_ID_HEADER, RequestIdMiddleware, setup_logging
from app.db.session import dispose_engine
from app.modules.health import router as health_routes
from app.modules.health.schemas import HealthResponse

log = logging.getLogger("neuroai")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    log.info(
        "startup",
        extra={
            "app": APP_NAME,
            "version": __version__,
            "app_env": settings.app_env,
            "worker_mode": app.state.worker_client.mode,
            "db": settings.database_url.split("://", 1)[0],
        },
    )
    yield
    await app.state.worker_client.aclose()
    await dispose_engine()
    log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="NeuroAI API",
        version=__version__,
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.worker_client = get_worker_client(settings)

    # add_middleware() prepends: first added = innermost. The 500 envelope must be built inside
    # CORS and RequestId so it still gets their headers.
    app.add_middleware(UnhandledErrorMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )
    app.add_middleware(RequestIdMiddleware)
    register_error_handlers(app)

    app.include_router(api_v1_router, prefix="/api/v1")
    # Root alias for docker healthchecks / T-01 DoD; same payload as /api/v1/health.
    app.add_api_route(
        "/health",
        health_routes.get_health,
        methods=["GET"],
        response_model=HealthResponse,
        include_in_schema=False,
    )
    return app


app = create_app()
