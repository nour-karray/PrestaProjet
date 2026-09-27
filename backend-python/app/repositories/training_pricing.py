from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.training_pricing import TrainingPricing


class TrainingPricingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_case(self, case_id: UUID, *, for_update: bool = False) -> TrainingPricing | None:
        statement = select(TrainingPricing).where(TrainingPricing.training_case_id == case_id)
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def add(self, pricing: TrainingPricing) -> None:
        self.session.add(pricing)
        self.session.flush()
