from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentAdministrator, DbSession
from app.schemas.training_program import (
    TrainingProgramCreate,
    TrainingProgramDayCreate,
    TrainingProgramDayUpdate,
    TrainingProgramItemCreate,
    TrainingProgramItemUpdate,
    TrainingProgramResponse,
    TrainingProgramReturnRequest,
    TrainingProgramUpdate,
)
from app.services.training_program import TrainingProgramService

router = APIRouter(prefix="/api/training-cases", tags=["training-programs"])


@router.get("/{case_id}/program", response_model=TrainingProgramResponse)
def get_program(
    case_id: UUID, session: DbSession, _: CurrentAdministrator
) -> TrainingProgramResponse:
    return TrainingProgramService(session).get(case_id)


@router.post("/{case_id}/program", response_model=TrainingProgramResponse, status_code=201)
def create_program(
    case_id: UUID,
    payload: TrainingProgramCreate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).create(case_id, payload, administrator.id)


@router.patch("/{case_id}/program", response_model=TrainingProgramResponse)
def update_program(
    case_id: UUID,
    payload: TrainingProgramUpdate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).update(case_id, payload, administrator.id)


@router.post("/{case_id}/program/submit", response_model=TrainingProgramResponse)
def submit_program(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> TrainingProgramResponse:
    return TrainingProgramService(session).submit(case_id, administrator.id)


@router.post("/{case_id}/program/return", response_model=TrainingProgramResponse)
def return_program(
    case_id: UUID,
    payload: TrainingProgramReturnRequest,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).return_to_preparation(
        case_id, payload.reason, administrator.id
    )


@router.post("/{case_id}/program/validate", response_model=TrainingProgramResponse)
def validate_program(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> TrainingProgramResponse:
    return TrainingProgramService(session).validate(case_id, administrator.id)


@router.post("/{case_id}/program/days", response_model=TrainingProgramResponse)
def add_day(
    case_id: UUID,
    payload: TrainingProgramDayCreate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).add_day(case_id, payload, administrator.id)


@router.patch("/{case_id}/program/days/{day_id}", response_model=TrainingProgramResponse)
def update_day(
    case_id: UUID,
    day_id: UUID,
    payload: TrainingProgramDayUpdate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).update_day(case_id, day_id, payload, administrator.id)


@router.delete("/{case_id}/program/days/{day_id}", response_model=TrainingProgramResponse)
def remove_day(
    case_id: UUID,
    day_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).remove_day(case_id, day_id, administrator.id)


@router.post(
    "/{case_id}/program/days/{day_id}/move-up",
    response_model=TrainingProgramResponse,
)
def move_day_up(
    case_id: UUID,
    day_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).move_day(case_id, day_id, -1, administrator.id)


@router.post(
    "/{case_id}/program/days/{day_id}/move-down",
    response_model=TrainingProgramResponse,
)
def move_day_down(
    case_id: UUID,
    day_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).move_day(case_id, day_id, 1, administrator.id)


@router.post(
    "/{case_id}/program/days/{day_id}/items",
    response_model=TrainingProgramResponse,
)
def add_item(
    case_id: UUID,
    day_id: UUID,
    payload: TrainingProgramItemCreate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).add_item(case_id, day_id, payload, administrator.id)


@router.patch("/{case_id}/program/items/{item_id}", response_model=TrainingProgramResponse)
def update_item(
    case_id: UUID,
    item_id: UUID,
    payload: TrainingProgramItemUpdate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).update_item(case_id, item_id, payload, administrator.id)


@router.delete("/{case_id}/program/items/{item_id}", response_model=TrainingProgramResponse)
def remove_item(
    case_id: UUID,
    item_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).remove_item(case_id, item_id, administrator.id)


@router.post(
    "/{case_id}/program/items/{item_id}/move-up",
    response_model=TrainingProgramResponse,
)
def move_item_up(
    case_id: UUID,
    item_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).move_item(case_id, item_id, -1, administrator.id)


@router.post(
    "/{case_id}/program/items/{item_id}/move-down",
    response_model=TrainingProgramResponse,
)
def move_item_down(
    case_id: UUID,
    item_id: UUID,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingProgramResponse:
    return TrainingProgramService(session).move_item(case_id, item_id, 1, administrator.id)
