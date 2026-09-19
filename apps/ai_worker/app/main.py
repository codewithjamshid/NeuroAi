"""NeuroAI AI worker — FastAPI app (TZ §4.7). Run: uv run uvicorn app.main:app --port 8001"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, File, Query, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from app import __version__, emotion, medllm, models, stt, tts
from app.auth import require_worker_key
from app.config import get_settings
from app.errors import ModelNotLoaded, install_error_handlers
from app.gpu import gpu_info
from app.schemas import (
    ErrorResponse,
    HealthResponse,
    MedLLMRequest,
    MedLLMResponse,
    STTResponse,
    TTSRequest,
    VoiceEmotionResponse,
)

log = logging.getLogger("ai_worker")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not settings.worker_key:
        log.warning("WORKER_KEY is empty — every model endpoint will answer 401")
    log.info("models: %s", models.load_enabled(settings))
    yield
    models.unload_all()


app = FastAPI(title="NeuroAI AI Worker", version=__version__, lifespan=lifespan)
install_error_handlers(app)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(models=models.statuses(), gpu=gpu_info(), version=__version__)


_ERRORS = {401: {"model": ErrorResponse}, 503: {"model": ErrorResponse}}
router = APIRouter(dependencies=[Depends(require_worker_key)], responses=_ERRORS)


@router.post("/stt", response_model=STTResponse)
async def stt_endpoint(
    audio: Annotated[UploadFile, File(description="audio/wav, 16 kHz mono")],
    lang: Annotated[str, Query()] = "uz",
    initial_prompt: Annotated[str | None, Query()] = None,
) -> STTResponse:
    if not stt.is_loaded():
        raise ModelNotLoaded(stt.NAME)
    wav = await audio.read()
    return await run_in_threadpool(stt.transcribe, wav, lang, initial_prompt)


@router.post(
    "/tts",
    response_class=Response,
    responses={200: {"content": {"audio/wav": {}}}, **_ERRORS},
)
async def tts_endpoint(body: TTSRequest) -> Response:
    if not tts.is_loaded():
        raise ModelNotLoaded(tts.NAME)
    wav = await run_in_threadpool(tts.synthesize, body.text, body.speed, body.style)
    return Response(content=wav, media_type="audio/wav")


@router.post("/voice-emotion", response_model=VoiceEmotionResponse)
async def voice_emotion_endpoint(
    audio: Annotated[UploadFile, File(description="audio/wav, 16 kHz mono")],
) -> VoiceEmotionResponse:
    if not emotion.is_loaded():
        raise ModelNotLoaded(emotion.NAME)
    wav = await audio.read()
    return await run_in_threadpool(emotion.analyze, wav)


@router.post("/medllm/summarize", response_model=MedLLMResponse)
async def medllm_summarize(body: MedLLMRequest) -> MedLLMResponse:
    if not medllm.is_loaded():
        raise ModelNotLoaded(medllm.NAME)
    return await run_in_threadpool(medllm.summarize, body.text, body.image_b64, body.task)


app.include_router(router)
