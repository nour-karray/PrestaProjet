from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.training_document import DocumentType, TrainingDocument


class TrainingDocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_case(self, case_id: UUID) -> list[TrainingDocument]:
        return list(
            self.session.scalars(
                select(TrainingDocument)
                .where(TrainingDocument.training_case_id == case_id)
                .order_by(TrainingDocument.created_at)
            )
        )

    def get(
        self, case_id: UUID, document_type: DocumentType, *, for_update: bool = False
    ) -> TrainingDocument | None:
        statement = select(TrainingDocument).where(
            TrainingDocument.training_case_id == case_id,
            TrainingDocument.document_type == document_type.value,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def add(self, document: TrainingDocument) -> None:
        self.session.add(document)
        self.session.flush()
