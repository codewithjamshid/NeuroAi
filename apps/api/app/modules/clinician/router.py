import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbDep, require_roles
from app.modules.clinician import service
from app.modules.clinician.schemas import ClinicianPatientOut, ClinicianSessionOut, DashboardOut
from app.modules.patients import service as patients_service
from app.modules.users.models import User

router = APIRouter(tags=["clinician"])

ClinicianDep = Depends(require_roles("clinician", "admin"))


@router.get("/clinician/patients", response_model=list[ClinicianPatientOut])
async def clinician_patients(db: DbDep, user: User = ClinicianDep) -> list[ClinicianPatientOut]:
    return await service.list_patients(db, user)


@router.get("/patients/{patient_id}/dashboard", response_model=DashboardOut)
async def patient_dashboard(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbDep,
    days: int = Query(default=14, ge=1, le=90),
) -> DashboardOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return await service.dashboard(db, patient, days)


@router.get("/clinician/patients/{patient_id}/sessions", response_model=list[ClinicianSessionOut])
async def clinician_sessions(
    patient_id: uuid.UUID,
    db: DbDep,
    user: User = ClinicianDep,
    limit: int = Query(default=30, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ClinicianSessionOut]:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return await service.list_sessions(db, patient, limit, offset)
