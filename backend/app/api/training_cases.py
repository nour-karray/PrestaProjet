from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentAdministrator, DbSession
from app.models.training_case import TrainingCaseStatus
from app.repositories.training_case import ActivityRepository, TrainingCaseRepository
from app.schemas.training_case import (
    ActivityResponse,
    DashboardResponse,
    SortField,
    StatusChangeRequest,
    TrainingCaseCreate,
    TrainingCaseListResponse,
    TrainingCaseResponse,
    TrainingCaseUpdate,
)
from app.services.training_case import TrainingCaseService

router = APIRouter(prefix="/api", tags=["training-cases"])


@router.get("/training-cases", response_model=TrainingCaseListResponse)
def list_training_cases(
    session: DbSession,
    _: CurrentAdministrator,
    reference: str | None = None,
    company_id: UUID | None = None,
    theme: str | None = None,
    status: TrainingCaseStatus | None = None,
    created_from: date | None = None,
    created_to: date | None = None,
    desired_start_from: date | None = None,
    desired_start_to: date | None = None,
    include_archived: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: SortField = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
) -> TrainingCaseListResponse:
    items, total = TrainingCaseRepository(session).list(
        reference=reference,
        company_id=company_id,
        theme=theme,
        status=status,
        created_from=created_from,
        created_to=created_to,
        desired_start_from=desired_start_from,
        desired_start_to=desired_start_to,
        include_archived=include_archived,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return TrainingCaseListResponse(
        items=[TrainingCaseResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/training-cases", response_model=TrainingCaseResponse, status_code=201)
def create_training_case(
    payload: TrainingCaseCreate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingCaseResponse:
    case = TrainingCaseService(session).create(payload, administrator.id)
    return TrainingCaseResponse.model_validate(case)


@router.get("/training-cases/{case_id}", response_model=TrainingCaseResponse)
def get_training_case(
    case_id: UUID, session: DbSession, _: CurrentAdministrator
) -> TrainingCaseResponse:
    return TrainingCaseResponse.model_validate(TrainingCaseService(session).get(case_id))


@router.patch("/training-cases/{case_id}", response_model=TrainingCaseResponse)
def update_training_case(
    case_id: UUID,
    payload: TrainingCaseUpdate,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingCaseResponse:
    case = TrainingCaseService(session).update(case_id, payload, administrator.id)
    return TrainingCaseResponse.model_validate(case)


@router.post("/training-cases/{case_id}/change-status", response_model=TrainingCaseResponse)
def change_status(
    case_id: UUID,
    payload: StatusChangeRequest,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingCaseResponse:
    case = TrainingCaseService(session).change_status(case_id, payload.status, administrator.id)
    return TrainingCaseResponse.model_validate(case)


@router.post("/training-cases/{case_id}/cancel", response_model=TrainingCaseResponse)
def cancel_case(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> TrainingCaseResponse:
    return TrainingCaseResponse.model_validate(
        TrainingCaseService(session).cancel(case_id, administrator.id)
    )


@router.post("/training-cases/{case_id}/close", response_model=TrainingCaseResponse)
def close_case(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> TrainingCaseResponse:
    return TrainingCaseResponse.model_validate(
        TrainingCaseService(session).close(case_id, administrator.id)
    )


@router.post("/training-cases/{case_id}/archive", response_model=TrainingCaseResponse)
def archive_case(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> TrainingCaseResponse:
    return TrainingCaseResponse.model_validate(
        TrainingCaseService(session).archive(case_id, administrator.id)
    )


@router.get("/training-cases/{case_id}/activity", response_model=list[ActivityResponse])
def get_activity(
    case_id: UUID, session: DbSession, _: CurrentAdministrator
) -> list[ActivityResponse]:
    TrainingCaseService(session).get(case_id)
    return [
        ActivityResponse.model_validate(item)
        for item in ActivityRepository(session).list_for_case(case_id)
    ]


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(session: DbSession, administrator: CurrentAdministrator) -> DashboardResponse:
    del administrator
    repository = TrainingCaseRepository(session)
    active, cancelled, archived = repository.dashboard_counts()
    recent, _total = repository.list(
        reference=None,
        company_id=None,
        theme=None,
        status=None,
        created_from=None,
        created_to=None,
        desired_start_from=None,
        desired_start_to=None,
        include_archived=False,
        page=1,
        page_size=5,
        sort_by="created_at",
        sort_order="desc",
    )
    return DashboardResponse(
        active_count=active,
        cancelled_count=cancelled,
        archived_count=archived,
        recent_cases=[TrainingCaseResponse.model_validate(item) for item in recent],
    )
