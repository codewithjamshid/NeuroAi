import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbDep, require_roles
from app.modules.patients import service
from app.modules.patients.schemas import (
    ConsentIn,
    ConsentOut,
    MoodIn,
    MoodOut,
    MoodTrendPoint,
    PatientCreate,
    PatientOut,
    PatientPatch,
    RedFlagOut,
    RedFlagPatch,
)
from app.modules.users.models import User

router = APIRouter(tags=["patients"])

EditorDep = Depends(require_roles("clinician", "caregiver", "admin"))
ClinicianDep = Depends(require_roles("clinician", "admin"))


@router.get("/patients", response_model=list[PatientOut])
async def list_patients(user: CurrentUser, db: DbDep) -> list[PatientOut]:
    return [PatientOut.model_validate(p) for p in await service.list_patients(db, user)]


@router.post("/patients", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: PatientCreate,
    db: DbDep,
    user: User = EditorDep,
) -> PatientOut:
    return PatientOut.model_validate(await service.create_patient(db, user, body))


@router.get("/patients/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: uuid.UUID, user: CurrentUser, db: DbDep) -> PatientOut:
    return PatientOut.model_validate(await service.get_patient_for_user(db, patient_id, user))


@router.patch("/patients/{patient_id}", response_model=PatientOut)
async def patch_patient(
    patient_id: uuid.UUID,
    body: PatientPatch,
    db: DbDep,
    user: User = EditorDep,
) -> PatientOut:
    patient = await service.get_patient_for_user(db, patient_id, user)
    return PatientOut.model_validate(await service.update_patient(db, patient, user, body))


@router.post(
    "/patients/{patient_id}/consent",
    response_model=ConsentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_consent(
    patient_id: uuid.UUID, body: ConsentIn, user: CurrentUser, db: DbDep
) -> ConsentOut:
    patient = await service.get_patient_for_user(db, patient_id, user)
    return ConsentOut.model_validate(await service.add_consent(db, patient, user, body))


@router.post(
    "/patients/{patient_id}/mood", response_model=MoodOut, status_code=status.HTTP_201_CREATED
)
async def add_mood(patient_id: uuid.UUID, body: MoodIn, user: CurrentUser, db: DbDep) -> MoodOut:
    patient = await service.get_patient_for_user(db, patient_id, user)
    return MoodOut.model_validate(await service.add_mood(db, patient, user, body.self_score))


@router.get("/patients/{patient_id}/mood/trend", response_model=list[MoodTrendPoint])
async def mood_trend(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbDep,
    days: int = Query(default=14, ge=1, le=90),
) -> list[MoodTrendPoint]:
    patient = await service.get_patient_for_user(db, patient_id, user)
    return await service.mood_trend(db, patient, days)


@router.get("/patients/{patient_id}/red-flags", response_model=list[RedFlagOut])
async def list_red_flags(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbDep,
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[RedFlagOut]:
    patient = await service.get_patient_for_user(db, patient_id, user)
    flags = await service.list_red_flags(db, patient, status, limit, offset)
    return [RedFlagOut.model_validate(f) for f in flags]


@router.patch("/red-flags/{flag_id}", response_model=RedFlagOut)
async def patch_red_flag(
    flag_id: uuid.UUID,
    body: RedFlagPatch,
    db: DbDep,
    user: User = ClinicianDep,
) -> RedFlagOut:
    return RedFlagOut.model_validate(await service.update_red_flag(db, flag_id, user, body))
