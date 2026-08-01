from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.company import Company, CompanyContact
from app.repositories.company import CompanyRepository, ContactRepository
from app.schemas.company import CompanyCreate, CompanyUpdate, ContactCreate, ContactUpdate


class CompanyService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.companies = CompanyRepository(session)
        self.contacts = ContactRepository(session)

    def get_company(self, company_id: UUID) -> Company:
        company = self.companies.get(company_id)
        if company is None:
            raise ApiError(404, "COMPANY_NOT_FOUND", "L’entreprise est introuvable.")
        return company

    def create_company(self, payload: CompanyCreate) -> Company:
        self._ensure_name_available(payload.name)
        company = Company(**payload.model_dump())
        self.companies.add(company)
        self.session.commit()
        return self.get_company(company.id)

    def update_company(self, company_id: UUID, payload: CompanyUpdate) -> Company:
        company = self.get_company(company_id)
        changes = payload.model_dump(exclude_unset=True)
        if "name" in changes:
            self._ensure_name_available(changes["name"], company.id)
        for field, value in changes.items():
            setattr(company, field, value)
        self.session.commit()
        return self.get_company(company.id)

    def archive_company(self, company_id: UUID) -> None:
        company = self.get_company(company_id)
        company.is_archived = True
        self.session.commit()

    def create_contact(self, company_id: UUID, payload: ContactCreate) -> CompanyContact:
        self.get_company(company_id)
        if payload.is_primary:
            self.contacts.clear_primary(company_id)
        contact = CompanyContact(company_id=company_id, **payload.model_dump())
        self.contacts.add(contact)
        self.session.commit()
        self.session.refresh(contact)
        return contact

    def update_contact(self, contact_id: UUID, payload: ContactUpdate) -> CompanyContact:
        contact = self._get_contact(contact_id)
        changes = payload.model_dump(exclude_unset=True)
        if changes.get("is_primary"):
            self.contacts.clear_primary(contact.company_id, contact.id)
        for field, value in changes.items():
            setattr(contact, field, value)
        self.session.commit()
        self.session.refresh(contact)
        return contact

    def delete_contact(self, contact_id: UUID) -> None:
        contact = self._get_contact(contact_id)
        self.contacts.delete(contact)
        self.session.commit()

    def _get_contact(self, contact_id: UUID) -> CompanyContact:
        contact = self.contacts.get(contact_id)
        if contact is None:
            raise ApiError(404, "CONTACT_NOT_FOUND", "Le contact est introuvable.")
        return contact

    def _ensure_name_available(self, name: str, exclude_id: UUID | None = None) -> None:
        if self.companies.get_by_name(name, exclude_id) is not None:
            raise ApiError(
                409,
                "COMPANY_NAME_CONFLICT",
                "Une entreprise portant ce nom existe déjà.",
            )
