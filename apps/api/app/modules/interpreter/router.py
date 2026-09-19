import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, Query, UploadFile

from app.api.deps import CurrentUser, DbDep, SettingsDep
from app.modules.interpreter import service
from app.modules.interpreter.schemas import (
    BoardOut,
    ConfirmIn,
    ConfirmOut,
    GuessOut,
    InterpretationOut,
)
from app.modules.patients import service as patients_service

router = APIRouter(tags=["interpreter"])


@router.post("/interpreter/guess", response_model=GuessOut)
async def guess(
    user: CurrentUser,
    db: DbDep,
    settings: SettingsDep,
    patient_id: Annotated[uuid.UUID, Form()],
    session_id: Annotated[uuid.UUID | None, Form()] = None,
    text: Annotated[str | None, Form()] = None,
    audio: Annotated[UploadFile | None, File()] = None,
) -> GuessOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    data = await audio.read() if audio is not None else None
    return await service.guess(
        db, settings, patient, user, audio=data, text=text, session_id=session_id
    )


@router.post("/interpreter/confirm", response_model=ConfirmOut)
async def confirm(
    body: ConfirmIn, user: CurrentUser, db: DbDep, settings: SettingsDep
) -> ConfirmOut:
    return await service.confirm(db, settings, user, body)


@router.get("/interpreter/board", response_model=BoardOut)
async def board(patient_id: uuid.UUID, user: CurrentUser, db: DbDep) -> BoardOut:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    return await service.board(db, patient)


@router.get("/patients/{patient_id}/interpretations", response_model=list[InterpretationOut])
async def list_interpretations(
    patient_id: uuid.UUID,
    user: CurrentUser,
    db: DbDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[InterpretationOut]:
    patient = await patients_service.get_patient_for_user(db, patient_id, user)
    rows = await service.list_interpretations(db, patient.id, limit, offset)
    return [InterpretationOut.model_validate(r) for r in rows]
