from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import ProviderCall


async def list_provider_calls(db: AsyncSession, limit: int, offset: int = 0) -> list[ProviderCall]:
    stmt = select(ProviderCall).order_by(ProviderCall.created_at.desc()).limit(limit).offset(offset)
    return list((await db.scalars(stmt)).all())
