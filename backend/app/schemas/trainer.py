from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.trainer import TrainerCVExtractionStatus
from app.schemas.company import clean_optional_text, validate_local_email


class TrainerFields(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    full_name: str = Field(min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    mobile_phone: str | None = Field(default=None, max_length=50)
    birth_date: str | None = Field(default=None, max_length=50)
    birth_place: str | None = Field(default=None, max_length=150)
    address: str | None = Field(default=None, max_length=300)
    company: str | None = Field(default=None, max_length=200)
    employer_address: str | None = Field(default=None, max_length=300)
    job_title: str | None = Field(default=None, max_length=200)
    years_experience: int | None = Field(default=None, ge=0, le=80)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    daily_rate: Decimal | None = Field(default=None, ge=0)
    city: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    linkedin_url: str | None = Field(default=None, max_length=300)
    website: str | None = Field(default=None, max_length=300)
    notes: str | None = None

    @field_validator(
        "first_name",
        "last_name",
        "full_name",
        "phone",
        "mobile_phone",
        "birth_date",
        "birth_place",
        "address",
        "company",
        "employer_address",
        "job_title",
        "city",
        "country",
        "linkedin_url",
        "website",
        "notes",
        mode="before",
    )
    @classmethod
    def clean_text(cls, value: object) -> object:
        return clean_optional_text(value) if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> object:
        return validate_local_email(value) if isinstance(value, str | type(None)) else value


class TrainerCreate(TrainerFields):
    pass


class TrainerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = None
    mobile_phone: str | None = None
    birth_date: str | None = None
    birth_place: str | None = None
    address: str | None = None
    company: str | None = None
    employer_address: str | None = None
    job_title: str | None = None
    years_experience: int | None = Field(default=None, ge=0, le=80)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    daily_rate: Decimal | None = Field(default=None, ge=0)
    city: str | None = None
    country: str | None = None
    linkedin_url: str | None = None
    website: str | None = None
    notes: str | None = None

    @field_validator(
        "first_name",
        "last_name",
        "full_name",
        "phone",
        "mobile_phone",
        "birth_date",
        "birth_place",
        "address",
        "company",
        "employer_address",
        "job_title",
        "city",
        "country",
        "linkedin_url",
        "website",
        "notes",
        mode="before",
    )
    @classmethod
    def clean_text(cls, value: object) -> object:
        return clean_optional_text(value) if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> object:
        return validate_local_email(value) if isinstance(value, str | type(None)) else value

    @model_validator(mode="after")
    def keep_full_name_required(self) -> "TrainerUpdate":
        if "full_name" in self.model_fields_set and self.full_name is None:
            raise ValueError("Le nom complet est obligatoire.")
        return self


class TrainerResponse(TrainerFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TrainerListResponse(BaseModel):
    items: list[TrainerResponse]
    total: int
    page: int
    page_size: int


class CvResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trainer_id: UUID | None
    original_filename: str
    mime_type: str
    file_size: int
    sha256: str
    uploaded_at: datetime
    extraction_status: TrainerCVExtractionStatus
    extraction_model: str | None
    extraction_duration_ms: int | None
    parsed_json: dict | None
    extraction_error: str | None
    extraction_error_code: str | None


class CVListResponse(BaseModel):
    items: list[CvResponse]
    total: int
    page: int
    page_size: int


class TrainerAssignment(BaseModel):
    trainer_id: UUID | None
