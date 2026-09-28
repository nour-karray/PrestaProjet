from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrainingCaseStatus(StrEnum):
    BROUILLON = "BROUILLON"
    DEMANDE_RECUE = "DEMANDE_RECUE"
    RECHERCHE_FORMATEUR = "RECHERCHE_FORMATEUR"
    FORMATEUR_PROPOSE = "FORMATEUR_PROPOSE"
    FORMATEUR_ACCEPTE = "FORMATEUR_ACCEPTE"
    BESOIN_A_COMPLETER = "BESOIN_A_COMPLETER"
    BESOIN_COMPLETE = "BESOIN_COMPLETE"
    PROGRAMME_EN_PREPARATION = "PROGRAMME_EN_PREPARATION"
    PROGRAMME_A_VALIDER = "PROGRAMME_A_VALIDER"
    PROGRAMME_VALIDE = "PROGRAMME_VALIDE"
    TARIFICATION_EN_PREPARATION = "TARIFICATION_EN_PREPARATION"
    TARIFICATION_A_VALIDER = "TARIFICATION_A_VALIDER"
    TARIFICATION_VALIDEE = "TARIFICATION_VALIDEE"
    DOCUMENTS_A_GENERER = "DOCUMENTS_A_GENERER"
    DOCUMENTS_GENERES = "DOCUMENTS_GENERES"
    TERMINE = "TERMINE"
    ANNULE = "ANNULE"
    ARCHIVE = "ARCHIVE"


class TrainingCaseCounter(Base):
    __tablename__ = "training_case_counters"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False)


class TrainingCase(Base):
    __tablename__ = "training_cases"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reference: Mapped[str] = mapped_column(String(20), unique=True)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"))
    primary_contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("company_contacts.id", ondelete="SET NULL")
    )
    trainer_id: Mapped[UUID | None] = mapped_column(ForeignKey("trainers.id", ondelete="SET NULL"))
    theme: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(40),
        default=TrainingCaseStatus.BROUILLON.value,
        server_default=TrainingCaseStatus.BROUILLON.value,
    )
    desired_start_date: Mapped[date | None] = mapped_column(Date)
    desired_end_date: Mapped[date | None] = mapped_column(Date)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("administrators.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    company = relationship("Company")
    primary_contact = relationship("CompanyContact")
    trainer = relationship("Trainer")
    training_need = relationship(
        "TrainingNeed",
        back_populates="training_case",
        cascade="all, delete-orphan",
        uselist=False,
    )
    training_program = relationship(
        "TrainingProgram",
        back_populates="training_case",
        cascade="all, delete-orphan",
        uselist=False,
    )
    training_pricing = relationship(
        "TrainingPricing",
        back_populates="training_case",
        cascade="all, delete-orphan",
        uselist=False,
    )
    documents = relationship(
        "TrainingDocument",
        back_populates="training_case",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list["ActivityLog"]] = relationship(
        back_populates="training_case",
        cascade="all, delete-orphan",
        order_by="ActivityLog.created_at.desc()",
    )

    __table_args__ = (
        Index("ix_training_cases_status", status),
        Index("ix_training_cases_company_id", company_id),
        Index("ix_training_cases_created_at", created_at),
        Index("ix_training_cases_theme", theme),
        Index("ix_training_cases_is_archived", is_archived),
        Index("ix_training_cases_trainer_id", trainer_id),
    )


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    administrator_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("administrators.id", ondelete="SET NULL")
    )
    training_case_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("training_cases.id", ondelete="CASCADE")
    )
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[UUID | None]
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    training_case: Mapped[TrainingCase | None] = relationship(back_populates="activities")

    __table_args__ = (Index("ix_activity_logs_training_case_id", training_case_id),)
