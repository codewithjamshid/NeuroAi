import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbDep, require_roles
from app.modules.patients import service as patients_service
from app.modules.reports import service
from app.modules.reports.schemas import Period, ReportOut
from app.modules.users.models import User

router = APIRouter(tags=["reports"])

ClinicianDep = Depends(require_roles("clinician", "admin"))


@router.post(
    "/patients/{patient_id}/reports/generate",
    response_model=ReportOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_report(
    patient_id: uuid.UUID,
    db: DbDep,
    user: User = ClinicianDep,
    period: Period = "7d",
) -> ReportOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return ReportOut.model_validate(await service.generate(db, patient, period))


@router.get("/patients/{patient_id}/reports", response_model=list[ReportOut])
async def list_reports(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbDep,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ReportOut]:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return [ReportOut.model_validate(r) for r in await service.list_reports(db, patient.id, limit)]
