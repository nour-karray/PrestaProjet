from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProgramItemType(StrEnum):
    MODULE = "MODULE"
    SUBMODULE = "SUBMODULE"


class PedagogicalMethod(StrEnum):
    EXPOSE = "EXPOSE"
    DEMONSTRATION = "DEMONSTRATION"
    EXERCICE_PRATIQUE = "EXERCICE_PRATIQUE"
    ETUDE_DE_CAS = "ETUDE_DE_CAS"
    MISE_EN_SITUATION = "MISE_EN_SITUATION"
    ECHANGE_COLLECTIF = "ECHANGE_COLLECTIF"
    EVALUATION = "EVALUATION"


class TrainingProgram(Base):
    __tablename__ = "training_programs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    training_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_cases.id", ondelete="CASCADE"), unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(250))
    general_objectives: Mapped[str | None] = mapped_column(Text)
    prerequisites: Mapped[str | None] = mapped_column(Text)
    evaluation_method: Mapped[str | None] = mapped_column(Text)
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
    training_case = relationship("TrainingCase", back_populates="training_program")
    days: Mapped[list["TrainingProgramDay"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
        order_by="TrainingProgramDay.position",
    )


class TrainingProgramDay(Base):
    __tablename__ = "training_program_days"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    training_program_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_programs.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(250))
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    program: Mapped[TrainingProgram] = relationship(back_populates="days")
    items: Mapped[list["TrainingProgramItem"]] = relationship(
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="TrainingProgramItem.position",
    )

    __table_args__ = (
        CheckConstraint("position > 0", name="ck_training_program_days_position_positive"),
        UniqueConstraint(
            "training_program_id",
            "position",
            name="uq_training_program_days_program_position",
        ),
    )


class TrainingProgramItem(Base):
    __tablename__ = "training_program_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    training_program_day_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_program_days.id", ondelete="CASCADE")
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("training_program_items.id", ondelete="CASCADE"), index=True
    )
    item_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(250))
    content: Mapped[str | None] = mapped_column(Text)
    theory_minutes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    practice_minutes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    day: Mapped[TrainingProgramDay] = relationship(back_populates="items")
    parent: Mapped["TrainingProgramItem | None"] = relationship(
        back_populates="children", remote_side="TrainingProgramItem.id"
    )
    children: Mapped[list["TrainingProgramItem"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="TrainingProgramItem.position",
        single_parent=True,
    )
    method_links: Mapped[list["TrainingProgramItemMethod"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('MODULE','SUBMODULE')",
            name="ck_training_program_items_type",
        ),
        CheckConstraint(
            "theory_minutes >= 0 AND practice_minutes >= 0",
            name="ck_training_program_items_durations_non_negative",
        ),
        CheckConstraint("position > 0", name="ck_training_program_items_position_positive"),
        CheckConstraint(
            "(item_type = 'MODULE' AND parent_id IS NULL) "
            "OR (item_type = 'SUBMODULE' AND parent_id IS NOT NULL)",
            name="ck_training_program_items_parent_by_type",
        ),
        Index("ix_training_program_items_day_id", "training_program_day_id"),
        Index(
            "uq_training_program_modules_day_position",
            "training_program_day_id",
            "position",
            unique=True,
            sqlite_where=parent_id.is_(None),
        ),
        Index(
            "uq_training_program_submodules_parent_position",
            "parent_id",
            "position",
            unique=True,
            sqlite_where=parent_id.is_not(None),
        ),
    )


class TrainingProgramItemMethod(Base):
    __tablename__ = "training_program_item_methods"

    training_program_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_program_items.id", ondelete="CASCADE"), primary_key=True
    )
    method: Mapped[str] = mapped_column(String(40), primary_key=True)
    item: Mapped[TrainingProgramItem] = relationship(back_populates="method_links")

    __table_args__ = (
        CheckConstraint(
            "method IN ('EXPOSE','DEMONSTRATION','EXERCICE_PRATIQUE','ETUDE_DE_CAS',"
            "'MISE_EN_SITUATION','ECHANGE_COLLECTIF','EVALUATION')",
            name="ck_training_program_item_methods_method",
        ),
    )
