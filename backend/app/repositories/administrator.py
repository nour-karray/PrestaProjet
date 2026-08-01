from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.administrator import Administrator


class AdministratorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, administrator_id: UUID) -> Administrator | None:
        return self.session.get(Administrator, administrator_id)

    def get_by_email(self, email: str) -> Administrator | None:
        statement = select(Administrator).where(Administrator.email == email.lower())
        return self.session.scalar(statement)

    def add(self, administrator: Administrator) -> Administrator:
        self.session.add(administrator)
        self.session.flush()
        return administrator
