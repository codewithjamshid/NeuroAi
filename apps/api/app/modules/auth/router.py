from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbDep
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginIn,
    LoginOut,
    MeOut,
    RefreshIn,
    RegisterIn,
    TokenPair,
    UserBrief,
)

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginOut)
async def login(body: LoginIn, db: DbDep) -> LoginOut:
    user = await service.login(db, body.email, body.password)
    access, refresh = service.issue_tokens(user)
    patient_id = await service.resolve_patient_id(db, user)
    brief = UserBrief(id=user.id, role=user.role, full_name=user.full_name, patient_id=patient_id)
    return LoginOut(access=access, refresh=refresh, user=brief)


@router.post("/auth/refresh", response_model=TokenPair)
async def refresh(body: RefreshIn, db: DbDep) -> TokenPair:
    user = await service.refresh(db, body.refresh)
    access, refresh_token = service.issue_tokens(user)
    return TokenPair(access=access, refresh=refresh_token)


@router.post("/auth/register", response_model=LoginOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, db: DbDep) -> LoginOut:
    user = await service.register(db, body)
    access, refresh_token = service.issue_tokens(user)
    brief = UserBrief(id=user.id, role=user.role, full_name=user.full_name)
    return LoginOut(access=access, refresh=refresh_token, user=brief)


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUser, db: DbDep) -> MeOut:
    return MeOut(
        id=user.id,
        role=user.role,
        full_name=user.full_name,
        email=user.email,
        locale=user.locale,
        patient_id=await service.resolve_patient_id(db, user),
    )
