from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentAdministrator, DbSession
from app.schemas.training_need import (
    TrainingNeedCreate,
    TrainingNeedResponse,
    TrainingNeedUpdate,
)
from app.services.training_need import TrainingNeedService

router = APIRouter(prefix="/api/training-cases", tags=["training-needs"])


@router.get("/{case_id}/need", response_model=TrainingNeedResponse)
def get_training_need(
    case_id: UUID, session: DbSession, _: CurrentAdministrator
) -> TrainingNeedResponse:
    return TrainingNeedResponse.model_validate(TrainingNeedService(session).get(case_id))


@router.post("/{case_id}/need", response_model=TrainingNeedResponse, status_code=201)
def create_training_need(
    case_id: UUID,
    payload: TrainingNeedCreate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingNeedResponse:
    need = TrainingNeedService(session).create(case_id, payload, administrator.id)
    return TrainingNeedResponse.model_validate(need)


@router.patch("/{case_id}/need", response_model=TrainingNeedResponse)
def update_training_need(
    case_id: UUID,
    payload: TrainingNeedUpdate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingNeedResponse:
    need = TrainingNeedService(session).update(case_id, payload, administrator.id)
    return TrainingNeedResponse.model_validate(need)


@router.post("/{case_id}/need/validate", response_model=TrainingNeedResponse)
def validate_training_need(
    case_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingNeedResponse:
    need = TrainingNeedService(session).validate(case_id, administrator.id)
    return TrainingNeedResponse.model_validate(need)
