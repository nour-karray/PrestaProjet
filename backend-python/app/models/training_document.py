from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentType(StrEnum):
    PROGRAM = "PROGRAM"
    QUOTE = "QUOTE"
    AGREEMENT = "AGREEMENT"
    ATTENDANCE_SHEET = "ATTENDANCE_SHEET"
    CERTIFICATE = "CERTIFICATE"


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    FAILED = "FAILED"


class TrainingDocument(Base):
    __tablename__ = "training_documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    training_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_cases.id", ondelete="CASCADE"), index=True
    )
    document_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default=DocumentStatus.PENDING.value)
    display_name: Mapped[str] = mapped_column(String(150))
    internal_filename: Mapped[str | None] = mapped_column(String(255))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    relative_path: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    sha256: Mapped[str | None] = mapped_column(String(64))
    snapshot_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql")
    )
    generation_error: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    training_case = relationship("TrainingCase", back_populates="documents")

    __table_args__ = (
        UniqueConstraint(
            "training_case_id", "document_type", name="uq_training_documents_case_type"
        ),
        CheckConstraint(
            "document_type IN ('PROGRAM','QUOTE','AGREEMENT','ATTENDANCE_SHEET','CERTIFICATE')",
            name="ck_training_documents_type",
        ),
        CheckConstraint(
            "status IN ('PENDING','GENERATED','FAILED')",
            name="ck_training_documents_status",
        ),
    )
