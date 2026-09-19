"""FastAPI application factory. `uvicorn app.main:app`."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.db.registry  # noqa: F401  (models must be imported before any query/relationship)
from app import APP_NAME, __version__
from app.ai.worker.client import get_worker_client
from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.errors import UnhandledErrorMiddleware, register_error_handlers
from app.core.hooks import run_shutdown, run_startup
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
    await run_startup(app)  # module hooks: telegram poller, provider_calls sink, …
    yield
    await run_shutdown(app)
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
    # TZ §4.6: GET /media/tts/{file} — cached TTS wavs (MEDIA_DIR/tts). Also under /api/v1 so
    # NEXT_PUBLIC_API_URL-relative URLs work from the browser.
    tts_dir = settings.media_dir / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media/tts", StaticFiles(directory=tts_dir), name="media-tts")
    app.mount("/api/v1/media/tts", StaticFiles(directory=tts_dir), name="media-tts-v1")
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
