import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbDep
from app.modules.caregiver import service
from app.modules.caregiver.schemas import CaregiverTodayOut, TipsOut
from app.modules.patients import service as patients_service

router = APIRouter(prefix="/caregiver", tags=["caregiver"])


@router.get("/patients/{patient_id}/today", response_model=CaregiverTodayOut)
async def caregiver_today(patient_id: uuid.UUID, user: CurrentUser, db: DbDep) -> CaregiverTodayOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return await service.today(db, patient)


@router.get("/patients/{patient_id}/tips", response_model=TipsOut)
async def caregiver_tips(patient_id: uuid.UUID, user: CurrentUser, db: DbDep) -> TipsOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return await service.tips(db, patient)
