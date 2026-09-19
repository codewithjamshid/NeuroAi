import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbDep
from app.modules.patients import service as patients_service
from app.modules.sessions import service
from app.modules.sessions.schemas import (
    EndOut,
    FaceMetricIn,
    MessageOut,
    PatientStateIn,
    PatientStateOut,
    SessionCreate,
    SessionOut,
    SessionSummary,
    StoredOut,
    TranscriptOut,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionCreate, user: CurrentUser, db: DbDep) -> SessionOut:
    patient = await patients_service.get_patient_for_user(db, body.patient_id, user)
    return SessionOut.model_validate(await service.create_session(db, patient, user, body.mode))


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: uuid.UUID, user: CurrentUser, db: DbDep) -> SessionOut:
    return SessionOut.model_validate(await service.get_session_for_user(db, session_id, user))


@router.post("/{session_id}/end", response_model=EndOut)
async def end_session(session_id: uuid.UUID, user: CurrentUser, db: DbDep) -> EndOut:
    session = await service.get_session_for_user(db, session_id, user)
    session = await service.end_session(db, session)
    return EndOut(summary=SessionSummary.model_validate(session.summary or {}))


@router.get("/{session_id}/transcript", response_model=TranscriptOut)
async def transcript(session_id: uuid.UUID, user: CurrentUser, db: DbDep) -> TranscriptOut:
    session = await service.get_session_for_user(db, session_id, user)
    messages = [
        MessageOut(
            id=m.id,
            role=m.role,
            modality=m.modality,
            text=m.text,
            audio_url=m.audio_path,
            stt_confidence=m.stt_confidence,
            stt_provider=m.stt_provider,
            created_at=m.created_at,
            llm_meta=m.llm_meta,
        )
        for m in await service.list_messages(db, session.id)
    ]
    return TranscriptOut(session=SessionOut.model_validate(session), messages=messages)


@router.post("/{session_id}/face-metrics", response_model=StoredOut)
async def face_metrics(
    session_id: uuid.UUID, batch: list[FaceMetricIn], user: CurrentUser, db: DbDep
) -> StoredOut:
    session = await service.get_session_for_user(db, session_id, user)
    return StoredOut(stored=await service.store_face_metrics(db, session.id, batch))


@router.get("/{session_id}/state", response_model=PatientStateOut)
async def get_state(session_id: uuid.UUID, user: CurrentUser, db: DbDep) -> PatientStateOut:
    session = await service.get_session_for_user(db, session_id, user)
    return await service.latest_state(db, session.id)


@router.post("/{session_id}/state", response_model=PatientStateOut)
async def post_state(
    session_id: uuid.UUID, body: PatientStateIn, user: CurrentUser, db: DbDep
) -> PatientStateOut:
    session = await service.get_session_for_user(db, session_id, user)
    return await service.store_state(db, session.id, body)
