from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.training_need import DeliveryMode


class TrainingNeedFields(BaseModel):
    target_audience: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=300)
    participant_count: int | None = Field(default=None, gt=0)
    delivery_mode: DeliveryMode | None = None
    duration_hours: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    objectives: str | None = None
    desired_start_date: date | None = None
    desired_end_date: date | None = None
    constraints: str | None = None

    @field_validator("target_audience", "location", "objectives", "constraints", mode="before")
    @classmethod
    def clean_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        return cleaned or None


class TrainingNeedCreate(TrainingNeedFields):
    pass


class TrainingNeedUpdate(TrainingNeedFields):
    pass


class TrainingNeedResponse(TrainingNeedFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    training_case_id: UUID
    is_validated: bool
    validated_at: datetime | None
    created_at: datetime
    updated_at: datetime
