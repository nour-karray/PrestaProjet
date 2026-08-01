import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized_email = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized_email):
            raise ValueError("L’adresse email est invalide.")
        return normalized_email


class AdministratorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class AuthResponse(BaseModel):
    administrator: AdministratorResponse
    message: str


class MessageResponse(BaseModel):
    message: str
