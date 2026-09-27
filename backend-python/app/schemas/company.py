from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def validate_local_email(value: str | None) -> str | None:
    cleaned = clean_optional_text(value)
    if cleaned is None:
        return None
    local, separator, domain = cleaned.rpartition("@")
    if not separator or not local or "." not in domain or domain.startswith("."):
        raise ValueError("L'adresse email n'est pas valide.")
    return cleaned.lower()


class CompanyFields(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=120)
    tax_identifier: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=300)
    notes: str | None = None

    @field_validator("*", mode="before")
    @classmethod
    def clean_text(cls, value: object) -> object:
        return clean_optional_text(value) if isinstance(value, str) else value


class CompanyCreate(CompanyFields):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=120)
    tax_identifier: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=300)
    notes: str | None = None

    @field_validator("*", mode="before")
    @classmethod
    def clean_text(cls, value: object) -> object:
        return clean_optional_text(value) if isinstance(value, str) else value


class ContactCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    job_title: str | None = Field(default=None, max_length=150)
    is_primary: bool = False

    @field_validator("full_name", "phone", "job_title", mode="before")
    @classmethod
    def clean_text(cls, value: object) -> object:
        return clean_optional_text(value) if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> object:
        return validate_local_email(value) if isinstance(value, str | type(None)) else value


class ContactUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    job_title: str | None = Field(default=None, max_length=150)
    is_primary: bool | None = None

    @field_validator("full_name", "phone", "job_title", mode="before")
    @classmethod
    def clean_text(cls, value: object) -> object:
        return clean_optional_text(value) if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> object:
        return validate_local_email(value) if isinstance(value, str | type(None)) else value


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    full_name: str
    email: str | None
    phone: str | None
    job_title: str | None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class CompanyResponse(CompanyFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class CompanyDetailResponse(CompanyResponse):
    contacts: list[ContactResponse]


class CompanyListItem(CompanyResponse):
    primary_contact: ContactResponse | None


class CompanyListResponse(BaseModel):
    items: list[CompanyListItem]
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    message: str
