from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentAdministrator, DbSession
from app.schemas.training_pricing import (
    TrainingPricingCreate,
    TrainingPricingResponse,
    TrainingPricingReturnRequest,
    TrainingPricingUpdate,
)
from app.services.training_pricing import TrainingPricingService

router = APIRouter(prefix="/api/training-cases", tags=["training-pricings"])


@router.get("/{case_id}/pricing", response_model=TrainingPricingResponse)
def get_pricing(
    case_id: UUID, session: DbSession, _: CurrentAdministrator
) -> TrainingPricingResponse:
    return TrainingPricingService(session).get(case_id)


@router.post("/{case_id}/pricing", response_model=TrainingPricingResponse, status_code=201)
def create_pricing(
    case_id: UUID,
    _: TrainingPricingCreate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingPricingResponse:
    return TrainingPricingService(session).create(case_id, administrator.id)


@router.patch("/{case_id}/pricing", response_model=TrainingPricingResponse)
def update_pricing(
    case_id: UUID,
    payload: TrainingPricingUpdate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingPricingResponse:
    return TrainingPricingService(session).update(case_id, payload, administrator.id)


@router.post("/{case_id}/pricing/submit", response_model=TrainingPricingResponse)
def submit_pricing(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> TrainingPricingResponse:
    return TrainingPricingService(session).submit(case_id, administrator.id)


@router.post("/{case_id}/pricing/return", response_model=TrainingPricingResponse)
def return_pricing(
    case_id: UUID,
    payload: TrainingPricingReturnRequest,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingPricingResponse:
    return TrainingPricingService(session).return_to_preparation(
        case_id, payload.reason, administrator.id
    )


@router.post("/{case_id}/pricing/validate", response_model=TrainingPricingResponse)
def validate_pricing(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> TrainingPricingResponse:
    return TrainingPricingService(session).validate(case_id, administrator.id)
