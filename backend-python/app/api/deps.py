from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import TokenType, decode_token
from app.db.session import get_db
from app.models.administrator import Administrator
from app.repositories.administrator import AdministratorRepository

DbSession = Annotated[Session, Depends(get_db)]


def get_current_administrator(
    session: DbSession,
    access_token: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> Administrator:
    if access_token is None:
        raise ApiError(
            status_code=401,
            code="AUTHENTICATION_REQUIRED",
            message="Vous devez vous connecter pour accéder à cette page.",
        )

    administrator_id = decode_token(access_token, TokenType.ACCESS)
    administrator = AdministratorRepository(session).get_by_id(administrator_id)

    if administrator is None:
        raise ApiError(
            status_code=401,
            code="ADMINISTRATOR_NOT_FOUND",
            message="Le compte associé à cette session est introuvable.",
        )

    if not administrator.is_active:
        raise ApiError(
            status_code=403,
            code="INACTIVE_ACCOUNT",
            message="Ce compte administrateur est désactivé.",
        )

    return administrator


CurrentAdministrator = Annotated[
    Administrator,
    Depends(get_current_administrator),
]
