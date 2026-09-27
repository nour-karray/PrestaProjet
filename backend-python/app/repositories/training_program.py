from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.training_program import (
    TrainingProgram,
    TrainingProgramDay,
    TrainingProgramItem,
)


class TrainingProgramRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_case(self, case_id: UUID, *, for_update: bool = False) -> TrainingProgram | None:
        statement = (
            select(TrainingProgram)
            .where(TrainingProgram.training_case_id == case_id)
            .options(
                selectinload(TrainingProgram.days)
                .selectinload(TrainingProgramDay.items)
                .selectinload(TrainingProgramItem.method_links)
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def add(self, program: TrainingProgram) -> None:
        self.session.add(program)
        self.session.flush()

    def get_day(
        self, program_id: UUID, day_id: UUID, *, for_update: bool = False
    ) -> TrainingProgramDay | None:
        statement = select(TrainingProgramDay).where(
            TrainingProgramDay.id == day_id,
            TrainingProgramDay.training_program_id == program_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def get_item(
        self, program_id: UUID, item_id: UUID, *, for_update: bool = False
    ) -> TrainingProgramItem | None:
        statement = (
            select(TrainingProgramItem)
            .join(TrainingProgramDay)
            .where(
                TrainingProgramItem.id == item_id,
                TrainingProgramDay.training_program_id == program_id,
            )
            .options(selectinload(TrainingProgramItem.method_links))
        )
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)
