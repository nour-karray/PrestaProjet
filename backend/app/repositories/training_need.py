from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.training_need import TrainingNeed


class TrainingNeedRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_case(
        self, training_case_id: UUID, *, for_update: bool = False
    ) -> TrainingNeed | None:
        statement = select(TrainingNeed).where(TrainingNeed.training_case_id == training_case_id)
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def add(self, need: TrainingNeed) -> None:
        self.session.add(need)
        self.session.flush()
