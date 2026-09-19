from fastapi import APIRouter, Depends, Query

from app.api.deps import DbDep, require_roles
from app.modules.observability import service
from app.modules.observability.schemas import ProviderCallOut
from app.modules.users.models import User

router = APIRouter(prefix="/observability", tags=["observability"])

StaffDep = Depends(require_roles("clinician", "admin"))


@router.get("/provider-calls", response_model=list[ProviderCallOut])
async def provider_calls(
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = StaffDep,
) -> list[ProviderCallOut]:
    rows = await service.list_provider_calls(db, limit, offset)
    return [ProviderCallOut.model_validate(r) for r in rows]
