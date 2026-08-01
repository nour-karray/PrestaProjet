from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.company import Company, CompanyContact


class CompanyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, company_id: UUID) -> Company | None:
        statement = (
            select(Company).where(Company.id == company_id).options(selectinload(Company.contacts))
        )
        return self.session.scalar(statement)

    def get_by_name(self, name: str, exclude_id: UUID | None = None) -> Company | None:
        statement = select(Company).where(func.lower(Company.name) == name.lower())
        if exclude_id is not None:
            statement = statement.where(Company.id != exclude_id)
        return self.session.scalar(statement)

    def list(
        self,
        search: str | None,
        city: str | None,
        country: str | None,
        include_archived: bool,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Company], int]:
        filters = []
        if not include_archived:
            filters.append(Company.is_archived.is_(False))
        if search:
            filters.append(Company.name.ilike(f"%{search}%"))
        if city:
            filters.append(Company.city.ilike(f"%{city}%"))
        if country:
            filters.append(Company.country.ilike(f"%{country}%"))

        count = self.session.scalar(select(func.count(Company.id)).where(*filters)) or 0
        order_column = Company.name if sort_by == "name" else Company.created_at
        order_expression = order_column.desc() if sort_order == "desc" else order_column.asc()
        statement = (
            select(Company)
            .where(*filters)
            .options(selectinload(Company.contacts))
            .order_by(order_expression)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement).unique()), count

    def add(self, company: Company) -> Company:
        self.session.add(company)
        self.session.flush()
        return company


class ContactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, contact_id: UUID) -> CompanyContact | None:
        return self.session.get(CompanyContact, contact_id)

    def list_for_company(self, company_id: UUID) -> list[CompanyContact]:
        statement = (
            select(CompanyContact)
            .where(CompanyContact.company_id == company_id)
            .order_by(CompanyContact.is_primary.desc(), CompanyContact.full_name)
        )
        return list(self.session.scalars(statement))

    def clear_primary(self, company_id: UUID, except_id: UUID | None = None) -> None:
        statement = update(CompanyContact).where(
            CompanyContact.company_id == company_id,
            CompanyContact.is_primary.is_(True),
        )
        if except_id is not None:
            statement = statement.where(CompanyContact.id != except_id)
        self.session.execute(statement.values(is_primary=False))

    def add(self, contact: CompanyContact) -> CompanyContact:
        self.session.add(contact)
        self.session.flush()
        return contact

    def delete(self, contact: CompanyContact) -> None:
        self.session.delete(contact)
