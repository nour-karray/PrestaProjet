from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.training_document import DocumentStatus, DocumentType


class TrainingDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    training_case_id: UUID
    document_type: DocumentType
    status: DocumentStatus
    display_name: str
    original_filename: str | None
    mime_type: str | None
    file_size: int | None
    sha256: str | None
    generation_error: str | None
    generated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DocumentGenerationResult(BaseModel):
    document_type: DocumentType
    success: bool
    document: TrainingDocumentResponse
    error: str | None = None


class GenerateAllResponse(BaseModel):
    results: list[DocumentGenerationResult]
    all_generated: bool
