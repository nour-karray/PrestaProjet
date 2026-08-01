from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.training_pricing import TrainerCostInitializationMethod

ALLOWED_VAT_RATES = {
    Decimal("19.000"),
    Decimal("13.000"),
    Decimal("7.000"),
    Decimal("0.000"),
}


def clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class TrainingPricingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TrainingPricingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trainer_cost: Decimal | None = Field(default=None, ge=0)
    transport_cost: Decimal | None = Field(default=None, ge=0)
    room_cost: Decimal | None = Field(default=None, ge=0)
    meal_cost: Decimal | None = Field(default=None, ge=0)
    other_cost: Decimal | None = Field(default=None, ge=0)
    margin_rate: Decimal | None = Field(default=None, ge=0, le=100)
    vat_rate: Decimal | None = None
    vat_exemption_reason: str | None = Field(default=None, max_length=2000)
    vat_legal_reference: str | None = Field(default=None, max_length=500)

    @field_validator("vat_rate")
    @classmethod
    def validate_vat_rate(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            raise ValueError("Le taux de TVA ne peut pas être vide.")
        if value not in ALLOWED_VAT_RATES:
            raise ValueError("Le taux de TVA doit être 19, 13, 7 ou 0 %.")
        return value

    @field_validator(
        "trainer_cost",
        "transport_cost",
        "room_cost",
        "meal_cost",
        "other_cost",
        "margin_rate",
    )
    @classmethod
    def reject_null_number(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            raise ValueError("La valeur ne peut pas être vide.")
        return value

    @field_validator("vat_exemption_reason", "vat_legal_reference", mode="before")
    @classmethod
    def clean_justification(cls, value: object) -> object:
        return clean_optional(value) if isinstance(value, str) else value


class TrainingPricingReturnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason", mode="before")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        return value.strip()


class TrainingPricingResponse(BaseModel):
    id: UUID
    training_case_id: UUID
    currency: str
    trainer_cost: Decimal
    transport_cost: Decimal
    room_cost: Decimal
    meal_cost: Decimal
    other_cost: Decimal
    margin_rate: Decimal
    margin_amount: Decimal
    total_costs: Decimal
    total_excluding_tax: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total_including_tax: Decimal
    vat_exemption_reason: str | None
    vat_legal_reference: str | None
    trainer_daily_rate_snapshot: Decimal | None
    trainer_hourly_rate_snapshot: Decimal | None
    program_day_count_snapshot: int
    program_duration_minutes_snapshot: int
    trainer_cost_initialization_method: TrainerCostInitializationMethod
    is_submitted: bool
    submitted_at: datetime | None
    is_validated: bool
    validated_at: datetime | None
    returned_at: datetime | None
    return_reason: str | None
    editable: bool
    created_at: datetime
    updated_at: datetime
