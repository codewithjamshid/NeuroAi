import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import ValidationError

from app.api.deps import CurrentUser, DbDep, SettingsDep, require_roles
from app.core.errors import AppError
from app.modules.exercises import service
from app.modules.exercises.schemas import (
    ExerciseTemplateOut,
    FaceSummary,
    NextOut,
    OkOut,
    SubmitOut,
)
from app.modules.patients.models import Patient
from app.modules.sessions import service as sessions_service
from app.modules.users.errors import NotFoundError
from app.modules.users.models import User

router = APIRouter(tags=["exercises"])

ClinicianDep = Depends(require_roles("clinician", "admin"))


@router.get(
    "/sessions/{session_id}/exercises/next",
    response_model=NextOut,
    response_model_exclude_none=True,
)
async def next_exercise(
    session_id: uuid.UUID, user: CurrentUser, db: DbDep, settings: SettingsDep
) -> NextOut:
    session = await sessions_service.get_session_for_user(db, session_id, user)
    patient = await db.get(Patient, session.patient_id)
    if patient is None:
        raise NotFoundError("Bemor topilmadi")
    return await service.next_item(db, settings, session, patient)


@router.post("/exercise-attempts/{attempt_id}/submit", response_model=SubmitOut)
async def submit_attempt(
    attempt_id: uuid.UUID,
    user: CurrentUser,
    db: DbDep,
    settings: SettingsDep,
    text: Annotated[str | None, Form()] = None,
    face_summary: Annotated[str | None, Form()] = None,
    response_ms: Annotated[int | None, Form(ge=0)] = None,
    audio: Annotated[UploadFile | None, File()] = None,
) -> SubmitOut:
    summary = None
    if face_summary:
        try:
            summary = FaceSummary.model_validate_json(face_summary)
        except ValidationError as exc:
            raise AppError(
                "face_summary noto'g'ri", code="validation_error", status_code=422
            ) from exc
    data = await audio.read() if audio is not None else None
    return await service.submit(
        db, settings, user, attempt_id,
        audio=data, text=text, face_summary=summary, response_ms=response_ms,
    )  # fmt: skip


@router.post("/exercise-attempts/{attempt_id}/skip", response_model=OkOut)
async def skip_attempt(attempt_id: uuid.UUID, user: CurrentUser, db: DbDep) -> OkOut:
    await service.skip(db, user, attempt_id)
    return OkOut()


@router.get("/exercise-templates", response_model=list[ExerciseTemplateOut])
async def list_templates(
    db: DbDep,
    category: str | None = None,
    level: Annotated[int | None, Query(ge=1, le=5)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
    user: User = ClinicianDep,
) -> list[ExerciseTemplateOut]:
    return await service.list_templates(db, category, level, limit, offset)
