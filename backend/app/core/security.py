from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.errors import ApiError

password_hash = PasswordHash.recommended()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_token(
    administrator_id: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(administrator_id),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(administrator_id: UUID) -> str:
    return create_token(
        administrator_id,
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(administrator_id: UUID) -> str:
    return create_token(
        administrator_id,
        TokenType.REFRESH,
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: TokenType) -> UUID:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as exc:
        raise ApiError(
            status_code=401,
            code="TOKEN_EXPIRED",
            message="Votre session a expiré. Veuillez vous reconnecter.",
        ) from exc
    except InvalidTokenError as exc:
        raise ApiError(
            status_code=401,
            code="INVALID_TOKEN",
            message="Le jeton d’authentification est invalide.",
        ) from exc

    if payload.get("type") != expected_type.value:
        raise ApiError(
            status_code=401,
            code="INVALID_TOKEN_TYPE",
            message="Le type de jeton d’authentification est invalide.",
        )

    try:
        return UUID(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiError(
            status_code=401,
            code="INVALID_TOKEN",
            message="Le jeton d’authentification est invalide.",
        ) from exc
