from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Response

from app.api.deps import CurrentAdministrator, DbSession
from app.core.config import settings
from app.core.errors import ApiError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.repositories.administrator import AdministratorRepository
from app.schemas.auth import (
    AdministratorResponse,
    AuthResponse,
    LoginRequest,
    MessageResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=int(timedelta(minutes=settings.access_token_expire_minutes).total_seconds()),
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=int(timedelta(days=settings.refresh_token_expire_days).total_seconds()),
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    session: DbSession,
) -> AuthResponse:
    administrator = AuthService(session).authenticate(
        payload.email,
        payload.password,
    )
    set_auth_cookies(
        response,
        create_access_token(administrator.id),
        create_refresh_token(administrator.id),
    )
    return AuthResponse(
        administrator=AdministratorResponse.model_validate(administrator),
        message="Connexion réussie.",
    )


@router.get("/me", response_model=AdministratorResponse)
def me(administrator: CurrentAdministrator) -> AdministratorResponse:
    return AdministratorResponse.model_validate(administrator)


@router.post("/refresh", response_model=MessageResponse)
def refresh(
    response: Response,
    session: DbSession,
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> MessageResponse:
    if refresh_token is None:
        raise ApiError(
            status_code=401,
            code="REFRESH_TOKEN_REQUIRED",
            message="Le jeton de renouvellement est absent.",
        )

    administrator_id = decode_token(refresh_token, TokenType.REFRESH)
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

    set_auth_cookies(
        response,
        create_access_token(administrator.id),
        create_refresh_token(administrator.id),
    )
    return MessageResponse(message="Session renouvelée.")


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response) -> MessageResponse:
    clear_auth_cookies(response)
    return MessageResponse(message="Déconnexion réussie.")
