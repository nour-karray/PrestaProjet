from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import verify_password
from app.models.administrator import Administrator
from app.repositories.administrator import AdministratorRepository


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.administrators = AdministratorRepository(session)

    def authenticate(self, email: str, password: str) -> Administrator:
        administrator = self.administrators.get_by_email(email)

        if administrator is None or not verify_password(
            password,
            administrator.password_hash,
        ):
            raise ApiError(
                status_code=401,
                code="INVALID_CREDENTIALS",
                message="L’adresse email ou le mot de passe est incorrect.",
            )

        if not administrator.is_active:
            raise ApiError(
                status_code=403,
                code="INACTIVE_ACCOUNT",
                message="Ce compte administrateur est désactivé.",
            )

        administrator.last_login_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(administrator)
        return administrator
