from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Query, Response, UploadFile

from app.api.deps import CurrentAdministrator, DbSession
from app.repositories.trainer import CVRepository, TrainerRepository
from app.schemas.trainer import (
    CVListResponse,
    CvResponse,
    TrainerAssignment,
    TrainerCreate,
    TrainerListResponse,
    TrainerResponse,
    TrainerUpdate,
)
from app.schemas.training_case import TrainingCaseResponse
from app.services.trainer import CVService, TrainerCVExtractionService, TrainerService

router = APIRouter(prefix="/api", tags=["trainers"])


@router.get("/trainers", response_model=TrainerListResponse)
def list_trainers(
    session: DbSession,
    _: CurrentAdministrator,
    search: str | None = None,
    include_inactive: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TrainerListResponse:
    items, total = TrainerRepository(session).list(search, include_inactive, page, page_size)
    return TrainerListResponse(
        items=[TrainerResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/trainers", response_model=TrainerResponse, status_code=201)
def create_trainer(
    payload: TrainerCreate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainerResponse:
    return TrainerResponse.model_validate(TrainerService(session).create(payload, administrator.id))


@router.get("/trainers/{trainer_id}", response_model=TrainerResponse)
def get_trainer(trainer_id: UUID, session: DbSession, _: CurrentAdministrator) -> TrainerResponse:
    return TrainerResponse.model_validate(TrainerService(session).get(trainer_id))


@router.patch("/trainers/{trainer_id}", response_model=TrainerResponse)
def update_trainer(
    trainer_id: UUID,
    payload: TrainerUpdate,
    session: DbSession,
    _: CurrentAdministrator,
) -> TrainerResponse:
    return TrainerResponse.model_validate(TrainerService(session).update(trainer_id, payload))


@router.delete("/trainers/{trainer_id}", response_model=TrainerResponse)
def archive_trainer(
    trainer_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainerResponse:
    return TrainerResponse.model_validate(
        TrainerService(session).archive(trainer_id, administrator.id)
    )


@router.get("/trainer-cvs", response_model=CVListResponse)
def list_cvs(
    session: DbSession,
    _: CurrentAdministrator,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CVListResponse:
    items, total = CVRepository(session).list(page, page_size)
    return CVListResponse(
        items=[CvResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/trainer-cvs/upload", response_model=CvResponse, status_code=201)
async def upload_cv(
    session: DbSession,
    administrator: CurrentAdministrator,
    file: Annotated[UploadFile, File()],
) -> CvResponse:
    cv = CVService(session).upload(
        file.filename,
        file.content_type or "",
        await file.read(),
        administrator.id,
    )
    return CvResponse.model_validate(cv)


@router.get("/trainer-cvs/{cv_id}", response_model=CvResponse)
def get_cv(cv_id: UUID, session: DbSession, _: CurrentAdministrator) -> CvResponse:
    return CvResponse.model_validate(CVService(session).get(cv_id))


@router.delete("/trainer-cvs/{cv_id}", status_code=204)
def delete_cv(
    cv_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> Response:
    CVService(session).delete(cv_id, administrator.id)
    return Response(status_code=204)


@router.post("/trainer-cvs/{cv_id}/extract", response_model=CvResponse)
def extract_cv(
    cv_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> CvResponse:
    cv = TrainerCVExtractionService(session).extract(cv_id, administrator.id)
    return CvResponse.model_validate(cv)


@router.post(
    "/trainer-cvs/{cv_id}/validate",
    response_model=TrainerResponse,
    status_code=201,
)
def validate_cv(
    cv_id: UUID,
    payload: TrainerCreate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainerResponse:
    trainer = CVService(session).validate(cv_id, payload, administrator.id)
    return TrainerResponse.model_validate(trainer)


@router.post("/training-cases/{case_id}/trainer", response_model=TrainingCaseResponse)
def assign_trainer(
    case_id: UUID,
    payload: TrainerAssignment,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingCaseResponse:
    training_case = TrainerService(session).assign_to_case(
        case_id, payload.trainer_id, administrator.id
    )
    return TrainingCaseResponse.model_validate(training_case)
