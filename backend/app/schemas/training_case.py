from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.training_case import TrainingCaseStatus
from app.schemas.company import ContactResponse


class TrainingCaseFields(BaseModel):
    company_id: UUID
    primary_contact_id: UUID | None = None
    theme: str = Field(min_length=1, max_length=250)
    description: str | None = None
    desired_start_date: date | None = None
    desired_end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "TrainingCaseFields":
        self.theme = " ".join(self.theme.split())
        if not self.theme:
            raise ValueError("Le thème est obligatoire.")
        if (
            self.desired_start_date
            and self.desired_end_date
            and self.desired_end_date < self.desired_start_date
        ):
            raise ValueError("La date de fin ne peut pas précéder la date de début.")
        return self


class TrainingCaseCreate(TrainingCaseFields):
    pass


class TrainingCaseUpdate(BaseModel):
    company_id: UUID | None = None
    primary_contact_id: UUID | None = None
    theme: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = None
    desired_start_date: date | None = None
    desired_end_date: date | None = None

    @field_validator("theme")
    @classmethod
    def clean_theme(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Le thème est obligatoire.")
        return cleaned


class StatusChangeRequest(BaseModel):
    status: TrainingCaseStatus


class CompanySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class TrainerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    job_title: str | None


class TrainingCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reference: str
    company: CompanySummary
    primary_contact: ContactResponse | None
    trainer: TrainerSummary | None
    theme: str
    description: str | None
    status: TrainingCaseStatus
    desired_start_date: date | None
    desired_end_date: date | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    is_archived: bool


class TrainingCaseListResponse(BaseModel):
    items: list[TrainingCaseResponse]
    total: int
    page: int
    page_size: int


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action: str
    details: dict
    created_at: datetime


class DashboardResponse(BaseModel):
    active_count: int
    cancelled_count: int
    archived_count: int
    recent_cases: list[TrainingCaseResponse]


SortField = Literal["created_at", "updated_at", "reference"]
