import uuid

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import CurrentUser, DbDep, require_roles
from app.modules.patients import service as patients_service
from app.modules.protocols import service
from app.modules.protocols.schemas import (
    ItemIn,
    ItemOut,
    ItemPatch,
    MedicationIn,
    MedicationOut,
    MedLogIn,
    MedLogOut,
    ProtocolCreate,
    ProtocolOut,
    ProtocolPatch,
    TemplateOut,
    TodayOut,
)
from app.modules.users.models import User

router = APIRouter(tags=["protocols"])

ClinicianDep = Depends(require_roles("clinician", "admin"))


@router.get("/protocol-templates", response_model=list[TemplateOut])
async def list_templates(_: CurrentUser) -> list[TemplateOut]:
    return service.load_templates()


@router.get("/patients/{patient_id}/protocol", response_model=ProtocolOut | None)
async def get_active_protocol(
    patient_id: uuid.UUID, user: CurrentUser, db: DbDep
) -> ProtocolOut | None:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    protocol = await service.get_active_protocol(db, patient.id)
    return ProtocolOut.model_validate(protocol) if protocol else None


@router.post(
    "/patients/{patient_id}/protocol",
    response_model=ProtocolOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_protocol(
    patient_id: uuid.UUID, body: ProtocolCreate, db: DbDep, user: User = ClinicianDep
) -> ProtocolOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return ProtocolOut.model_validate(await service.create_protocol(db, patient, user, body))


@router.patch("/protocols/{protocol_id}", response_model=ProtocolOut)
async def patch_protocol(
    protocol_id: uuid.UUID, body: ProtocolPatch, db: DbDep, user: User = ClinicianDep
) -> ProtocolOut:
    protocol = await service.get_protocol(db, protocol_id)
    await patients_service.get_patient_for_user(db, protocol.patient_id, user)
    return ProtocolOut.model_validate(await service.update_protocol(db, protocol, body))


@router.post(
    "/protocols/{protocol_id}/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED
)
async def add_item(
    protocol_id: uuid.UUID, body: ItemIn, db: DbDep, user: User = ClinicianDep
) -> ItemOut:
    protocol = await service.get_protocol(db, protocol_id)
    await patients_service.get_patient_for_user(db, protocol.patient_id, user)
    return ItemOut.model_validate(await service.add_item(db, protocol, body))


@router.patch("/protocol-items/{item_id}", response_model=ItemOut)
async def patch_item(
    item_id: uuid.UUID, body: ItemPatch, db: DbDep, user: User = ClinicianDep
) -> ItemOut:
    item = await service.get_item(db, item_id)
    protocol = await service.get_protocol(db, item.protocol_id)
    await patients_service.get_patient_for_user(db, protocol.patient_id, user)
    return ItemOut.model_validate(await service.update_item(db, item, body))


@router.delete("/protocol-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: uuid.UUID, db: DbDep, user: User = ClinicianDep) -> Response:
    item = await service.get_item(db, item_id)
    protocol = await service.get_protocol(db, item.protocol_id)
    await patients_service.get_patient_for_user(db, protocol.patient_id, user)
    await service.delete_item(db, item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/patients/{patient_id}/medications", response_model=list[MedicationOut])
async def list_medications(
    patient_id: uuid.UUID, user: CurrentUser, db: DbDep
) -> list[MedicationOut]:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    meds = await service.list_medications(db, patient.id)
    return [MedicationOut.model_validate(m) for m in meds]


@router.post(
    "/patients/{patient_id}/medications",
    response_model=MedicationOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_medication(
    patient_id: uuid.UUID, body: MedicationIn, db: DbDep, user: User = ClinicianDep
) -> MedicationOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return MedicationOut.model_validate(await service.add_medication(db, patient.id, body))


@router.post(
    "/medications/{medication_id}/log",
    response_model=MedLogOut,
    status_code=status.HTTP_201_CREATED,
)
async def log_medication(
    medication_id: uuid.UUID, body: MedLogIn, user: CurrentUser, db: DbDep
) -> MedLogOut:
    med = await service.get_medication(db, medication_id)
    await patients_service.get_patient_for_user(db, med.patient_id, user)
    return MedLogOut.model_validate(await service.log_medication(db, med, user, body))


@router.get("/patients/{patient_id}/today", response_model=TodayOut)
async def today(patient_id: uuid.UUID, user: CurrentUser, db: DbDep) -> TodayOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return await service.build_today(db, patient)
