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


# --- T-02 (backend-core): DB session, current user, RBAC ---------------------------------------
import uuid  # noqa: E402
from collections.abc import Callable, Coroutine  # noqa: E402
from typing import Any  # noqa: E402

import jwt  # noqa: E402
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db.session import get_db  # noqa: E402
from app.modules.auth.security import decode_token  # noqa: E402
from app.modules.users.errors import ForbiddenError, UnauthorizedError  # noqa: E402
from app.modules.users.models import User  # noqa: E402

DbDep = Annotated[AsyncSession, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """401 `unauthorized` for a missing/invalid/expired access token or inactive user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Token yo'q")
    try:
        claims = decode_token(credentials.credentials, "access")
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise UnauthorizedError("Token yaroqsiz") from exc
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Foydalanuvchi topilmadi")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: str) -> Callable[..., Coroutine[Any, Any, User]]:
    """`user: User = Depends(require_roles("clinician", "admin"))` → 403 `forbidden` otherwise."""

    async def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError("Ruxsat yo'q")
        return user

    return _check
