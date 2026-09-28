from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrainerCVExtractionStatus(StrEnum):
    UPLOADED = "UPLOADED"
    TEXT_EXTRACTED = "TEXT_EXTRACTED"
    OCR_REQUIRED = "OCR_REQUIRED"
    OCR_COMPLETED = "OCR_COMPLETED"
    AI_ANALYSIS_PENDING = "AI_ANALYSIS_PENDING"
    AI_ANALYSIS_COMPLETED = "AI_ANALYSIS_COMPLETED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAILED = "FAILED"
    VALIDATED = "VALIDATED"


class Trainer(Base):
    __tablename__ = "trainers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile_phone: Mapped[str | None] = mapped_column(String(50))
    birth_date: Mapped[str | None] = mapped_column(String(50))
    birth_place: Mapped[str | None] = mapped_column(String(150))
    address: Mapped[str | None] = mapped_column(String(300))
    company: Mapped[str | None] = mapped_column(String(200), index=True)
    employer_address: Mapped[str | None] = mapped_column(String(300))
    job_title: Mapped[str | None] = mapped_column(String(200))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    daily_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    city: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(120))
    linkedin_url: Mapped[str | None] = mapped_column(String(300))
    website: Mapped[str | None] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    cvs: Mapped[list["TrainerCV"]] = relationship(back_populates="trainer")

    __table_args__ = (
        CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="ck_trainers_years_experience_non_negative",
        ),
        CheckConstraint(
            "hourly_rate IS NULL OR hourly_rate >= 0",
            name="ck_trainers_hourly_rate_non_negative",
        ),
        CheckConstraint(
            "daily_rate IS NULL OR daily_rate >= 0",
            name="ck_trainers_daily_rate_non_negative",
        ),
    )


class TrainerCV(Base):
    __tablename__ = "trainer_cvs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    trainer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("trainers.id", ondelete="SET NULL"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_filename: Mapped[str] = mapped_column(String(255), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    extraction_status: Mapped[str] = mapped_column(
        String(32),
        default=TrainerCVExtractionStatus.UPLOADED.value,
        server_default=TrainerCVExtractionStatus.UPLOADED.value,
    )
    extraction_model: Mapped[str | None] = mapped_column(String(120))
    extraction_duration_ms: Mapped[int | None] = mapped_column(Integer)
    raw_text: Mapped[str | None] = mapped_column(Text)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    extraction_error: Mapped[str | None] = mapped_column(Text)
    extraction_error_code: Mapped[str | None] = mapped_column(String(64))
    trainer: Mapped[Trainer | None] = relationship(back_populates="cvs")

    __table_args__ = (
        UniqueConstraint("sha256"),
        Index("ix_trainer_cvs_sha256", sha256),
    )
