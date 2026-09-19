from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbDep, SettingsDep
from app.modules.notifications import service
from app.modules.notifications.schemas import LinkOut, LinkStatusOut, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/telegram/link", response_model=LinkOut)
async def telegram_link(user: CurrentUser, settings: SettingsDep) -> LinkOut:
    code = service.create_link_code(user.id)
    return LinkOut(code=code, bot_username=await service.bot_username(settings))


@router.get("/telegram/status", response_model=LinkStatusOut)
async def telegram_status(user: CurrentUser) -> LinkStatusOut:
    return LinkStatusOut(**await service.link_status(user))


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    user: CurrentUser, db: DbDep, limit: int = Query(default=20, ge=1, le=100)
) -> list[NotificationOut]:
    rows = await service.list_notifications(db, user, limit)
    return [NotificationOut.model_validate(r) for r in rows]
