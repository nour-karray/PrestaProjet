from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.api.deps import CurrentAdministrator, DbSession
from app.models.training_document import DocumentType
from app.schemas.training_document import GenerateAllResponse, TrainingDocumentResponse
from app.services.training_document import TrainingDocumentService

router = APIRouter(prefix="/api/training-cases", tags=["training-documents"])


@router.get("/{case_id}/documents", response_model=list[TrainingDocumentResponse])
def list_documents(
    case_id: UUID, session: DbSession, _: CurrentAdministrator
) -> list[TrainingDocumentResponse]:
    return TrainingDocumentService(session).list_documents(case_id)


@router.post("/{case_id}/documents/initialize", response_model=list[TrainingDocumentResponse])
def initialize_documents(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> list[TrainingDocumentResponse]:
    return TrainingDocumentService(session).initialize(case_id, administrator.id)


@router.post("/{case_id}/documents/generate-all", response_model=GenerateAllResponse)
def generate_all_documents(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> GenerateAllResponse:
    return TrainingDocumentService(session).generate_all(case_id, administrator.id)


@router.post(
    "/{case_id}/documents/{document_type}/generate",
    response_model=TrainingDocumentResponse,
)
def generate_document(
    case_id: UUID,
    document_type: DocumentType,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> TrainingDocumentResponse:
    return TrainingDocumentService(session).generate(case_id, document_type, administrator.id)


@router.get("/{case_id}/documents/{document_type}/download")
def download_document(
    case_id: UUID,
    document_type: DocumentType,
    session: DbSession,
    administrator: CurrentAdministrator,
) -> FileResponse:
    path, filename = TrainingDocumentService(session).download(
        case_id, document_type, administrator.id
    )
    return FileResponse(path, media_type="application/pdf", filename=filename)
