import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import CurrentUser, DbDep, SettingsDep
from app.modules.companion import service
from app.modules.companion.schemas import ConfirmIn, MessageResponse
from app.modules.patients import service as patients_service
from app.modules.sessions import service as sessions_service

router = APIRouter(tags=["companion"])

MAX_AUDIO_BYTES = 8 * 1024 * 1024


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def post_message(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DbDep,
    settings: SettingsDep,
    audio: Annotated[UploadFile | None, File()] = None,
    text: Annotated[str | None, Form()] = None,
    pictogram_key: Annotated[str | None, Form()] = None,
    face_batch: Annotated[str | None, Form()] = None,
    latency_ms: Annotated[int | None, Form()] = None,
) -> MessageResponse:
    session = await sessions_service.get_session_for_user(db, session_id, user)
    patient = await patients_service.get_patient_for_user(db, session.patient_id, user)
    audio_bytes = (await audio.read(MAX_AUDIO_BYTES)) if audio is not None else None
    turn = service.TurnInput(
        audio=audio_bytes or None,
        text=text,
        pictogram_key=pictogram_key,
        face_batch=service.parse_face_batch(face_batch),
        latency_ms=latency_ms,
    )
    return await service.handle_turn(db, settings, session, patient, turn)


@router.post("/sessions/{session_id}/confirm", response_model=MessageResponse)
async def confirm(
    session_id: uuid.UUID, body: ConfirmIn, user: CurrentUser, db: DbDep, settings: SettingsDep
) -> MessageResponse:
    session = await sessions_service.get_session_for_user(db, session_id, user)
    patient = await patients_service.get_patient_for_user(db, session.patient_id, user)
    return await service.confirm(db, settings, session, patient, body.candidate_key)
