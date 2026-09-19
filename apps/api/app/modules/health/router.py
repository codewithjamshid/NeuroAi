from fastapi import APIRouter

from app.api.deps import SettingsDep, WorkerDep
from app.modules.health import service
from app.modules.health.schemas import HealthResponse, ProvidersHealth

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def get_health(settings: SettingsDep) -> HealthResponse:
    return service.get_health(settings)


@router.get("/providers", response_model=ProvidersHealth)
async def get_providers_health(settings: SettingsDep, client: WorkerDep) -> ProvidersHealth:
    return await service.get_providers_health(settings, client)
