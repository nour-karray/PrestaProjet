from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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


class DeliveryMode(StrEnum):
    PRESENTIEL = "PRESENTIEL"
    DISTANCIEL = "DISTANCIEL"
    HYBRIDE = "HYBRIDE"


class TrainingNeedLevel(StrEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class TrainingNeed(Base):
    __tablename__ = "training_needs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    training_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_cases.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    target_audience: Mapped[str | None] = mapped_column(String(500))
    level: Mapped[str | None] = mapped_column(String(20))
    location: Mapped[str | None] = mapped_column(String(300))
    participant_count: Mapped[int | None] = mapped_column(Integer)
    delivery_mode: Mapped[str | None] = mapped_column(String(20))
    duration_hours: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    planned_days_count: Mapped[int | None] = mapped_column(Integer)
    objectives: Mapped[str | None] = mapped_column(Text)
    desired_start_date: Mapped[date | None] = mapped_column(Date)
    desired_end_date: Mapped[date | None] = mapped_column(Date)
    constraints: Mapped[str | None] = mapped_column(Text)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    training_case = relationship("TrainingCase", back_populates="training_need")

    __table_args__ = (
        CheckConstraint(
            "participant_count IS NULL OR participant_count > 0",
            name="ck_training_needs_participant_count_positive",
        ),
        CheckConstraint(
            "duration_hours IS NULL OR duration_hours > 0",
            name="ck_training_needs_duration_hours_positive",
        ),
        CheckConstraint(
            "planned_days_count IS NULL OR planned_days_count > 0",
            name="ck_training_needs_planned_days_count_positive",
        ),
        CheckConstraint(
            "delivery_mode IS NULL OR delivery_mode IN ('PRESENTIEL','DISTANCIEL','HYBRIDE')",
            name="ck_training_needs_delivery_mode",
        ),
        CheckConstraint(
            "level IS NULL OR level IN ('BEGINNER','INTERMEDIATE','ADVANCED','EXPERT')",
            name="ck_training_needs_level",
        ),
        CheckConstraint(
            "desired_end_date IS NULL OR desired_start_date IS NULL "
            "OR desired_end_date >= desired_start_date",
            name="ck_training_needs_date_range",
        ),
    )
