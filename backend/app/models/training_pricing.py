from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrainerCostInitializationMethod(StrEnum):
    DAILY_RATE = "DAILY_RATE"
    HOURLY_RATE = "HOURLY_RATE"
    NONE = "NONE"


class TrainingPricing(Base):
    __tablename__ = "training_pricings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    training_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_cases.id", ondelete="CASCADE"), unique=True, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), default="TND", server_default="TND")
    trainer_cost: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0, server_default="0")
    transport_cost: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0, server_default="0")
    room_cost: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0, server_default="0")
    meal_cost: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0, server_default="0")
    other_cost: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0, server_default="0")
    margin_rate: Mapped[Decimal] = mapped_column(Numeric(6, 3), default=0, server_default="0")
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(6, 3), default=19, server_default="19")
    vat_exemption_reason: Mapped[str | None] = mapped_column(Text)
    vat_legal_reference: Mapped[str | None] = mapped_column(String(500))
    trainer_daily_rate_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(15, 3))
    trainer_hourly_rate_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(15, 3))
    program_day_count_snapshot: Mapped[int] = mapped_column(Integer)
    program_duration_minutes_snapshot: Mapped[int] = mapped_column(Integer)
    trainer_cost_initialization_method: Mapped[str] = mapped_column(String(20))
    is_submitted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    return_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    training_case = relationship("TrainingCase", back_populates="training_pricing")

    __table_args__ = (
        CheckConstraint("currency = 'TND'", name="ck_training_pricings_currency"),
        CheckConstraint(
            "trainer_cost >= 0 AND transport_cost >= 0 AND room_cost >= 0 "
            "AND meal_cost >= 0 AND other_cost >= 0",
            name="ck_training_pricings_costs_non_negative",
        ),
        CheckConstraint(
            "margin_rate >= 0 AND margin_rate <= 100",
            name="ck_training_pricings_margin_rate",
        ),
        CheckConstraint(
            "vat_rate IN (19.000, 13.000, 7.000, 0.000)",
            name="ck_training_pricings_vat_rate",
        ),
        CheckConstraint(
            "vat_rate <> 0 OR vat_exemption_reason IS NOT NULL OR vat_legal_reference IS NOT NULL",
            name="ck_training_pricings_zero_vat_justification",
        ),
        CheckConstraint(
            "program_day_count_snapshot >= 0 AND program_duration_minutes_snapshot >= 0",
            name="ck_training_pricings_program_snapshots_non_negative",
        ),
        CheckConstraint(
            "trainer_cost_initialization_method IN ('DAILY_RATE','HOURLY_RATE','NONE')",
            name="ck_training_pricings_initialization_method",
        ),
    )
