from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentAdministrator, DbSession
from app.repositories.company import CompanyRepository, ContactRepository
from app.schemas.company import (
    CompanyCreate,
    CompanyDetailResponse,
    CompanyListItem,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    MessageResponse,
)
from app.services.company import CompanyService

router = APIRouter(prefix="/api", tags=["companies"])


@router.get("/companies", response_model=CompanyListResponse)
def list_companies(
    session: DbSession,
    _: CurrentAdministrator,
    search: str | None = None,
    city: str | None = None,
    country: str | None = None,
    include_archived: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: Literal["name", "created_at"] = "name",
    sort_order: Literal["asc", "desc"] = "asc",
) -> CompanyListResponse:
    companies, total = CompanyRepository(session).list(
        search, city, country, include_archived, page, page_size, sort_by, sort_order
    )
    items = []
    for company in companies:
        primary = next((contact for contact in company.contacts if contact.is_primary), None)
        items.append(
            CompanyListItem(
                **CompanyResponse.model_validate(company).model_dump(),
                primary_contact=ContactResponse.model_validate(primary) if primary else None,
            )
        )
    return CompanyListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/companies", response_model=CompanyDetailResponse, status_code=201)
def create_company(
    payload: CompanyCreate, session: DbSession, _: CurrentAdministrator
) -> CompanyDetailResponse:
    return CompanyDetailResponse.model_validate(CompanyService(session).create_company(payload))


@router.get("/companies/{company_id}", response_model=CompanyDetailResponse)
def get_company(
    company_id: UUID, session: DbSession, _: CurrentAdministrator
) -> CompanyDetailResponse:
    return CompanyDetailResponse.model_validate(CompanyService(session).get_company(company_id))


@router.patch("/companies/{company_id}", response_model=CompanyDetailResponse)
def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    session: DbSession,
    _: CurrentAdministrator,
) -> CompanyDetailResponse:
    return CompanyDetailResponse.model_validate(
        CompanyService(session).update_company(company_id, payload)
    )


@router.delete("/companies/{company_id}", response_model=MessageResponse)
def archive_company(
    company_id: UUID, session: DbSession, _: CurrentAdministrator
) -> MessageResponse:
    CompanyService(session).archive_company(company_id)
    return MessageResponse(message="L’entreprise a été archivée.")


@router.get("/companies/{company_id}/contacts", response_model=list[ContactResponse])
def list_contacts(
    company_id: UUID, session: DbSession, _: CurrentAdministrator
) -> list[ContactResponse]:
    CompanyService(session).get_company(company_id)
    return [
        ContactResponse.model_validate(contact)
        for contact in ContactRepository(session).list_for_company(company_id)
    ]


@router.post(
    "/companies/{company_id}/contacts",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(
    company_id: UUID,
    payload: ContactCreate,
    session: DbSession,
    _: CurrentAdministrator,
) -> ContactResponse:
    return ContactResponse.model_validate(
        CompanyService(session).create_contact(company_id, payload)
    )


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    session: DbSession,
    _: CurrentAdministrator,
) -> ContactResponse:
    return ContactResponse.model_validate(
        CompanyService(session).update_contact(contact_id, payload)
    )


@router.delete("/contacts/{contact_id}", response_model=MessageResponse)
def delete_contact(
    contact_id: UUID, session: DbSession, _: CurrentAdministrator
) -> MessageResponse:
    CompanyService(session).delete_contact(contact_id)
    return MessageResponse(message="Le contact a été supprimé.")
