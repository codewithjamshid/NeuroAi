from fastapi import APIRouter

from app.api.deps import CurrentUser, SettingsDep
from app.modules.tts import service
from app.modules.tts.schemas import TTSIn, TTSOut

router = APIRouter(tags=["tts"])


@router.post("/tts", response_model=TTSOut)
async def synthesize(body: TTSIn, user: CurrentUser, settings: SettingsDep) -> TTSOut:
    """Any authenticated role; the client keys its own cache on the text, the server on sha1."""
    return await service.synthesize(settings, body.text, body.speed)
