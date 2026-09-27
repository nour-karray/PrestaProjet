from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic.runtime.migration import MigrationContext
from app.core.config import settings
from app.models.administrator import Administrator
from app.models.company import Company, CompanyContact
from app.models.trainer import Trainer, TrainerCV, TrainerCVExtractionStatus
from app.models.training_case import TrainingCase
from app.models.training_document import DocumentStatus
from app.repositories.training_case import TrainingCaseRepository
from app.schemas.trainer import TrainerCreate
from app.services.cv_text_extractor import CVTextExtractionResult, CVTextExtractor
from app.services.trainer import CVService, TrainerCVExtractionService
from app.services.training_document import TrainingDocumentService
from app.storage.documents import DocumentStorage
from app.tests.test_training_documents import make_ready_case

EXPECTED_REVISION = "20260730_0012"


class _PostgresTextExtractor(CVTextExtractor):
    def extract(self, path: Path, mime_type: str) -> CVTextExtractionResult:
        del path, mime_type
        text = "Karim Test formateur professionnel karim@example.com Tunis Tunisie"
        return CVTextExtractionResult(text, 1, len(text))


class _PostgresLLM:
    model_name: str | None = "integration-model"

    def __init__(self, unavailable: bool = False) -> None:
        self.unavailable = unavailable

    def generate_structured(self, prompt, response_schema):
        del prompt, response_schema
        if self.unavailable:
            from app.core.errors import ApiError

            raise ApiError(503, "LLM_UNAVAILABLE", "Ollama indisponible.")
        return {
            "first_name": "Karim", "last_name": "Test", "full_name": "Karim Test",
            "email": "karim@example.com", "phone": None, "company": None,
            "job_title": "Formateur", "years_experience": 8, "city": "Tunis",
            "country": "Tunisie", "linkedin_url": None, "website": None,
            "summary": None, "skills": [], "languages": [], "certifications": [],
            "education": [], "experiences": [], "confidence": {}, "warnings": [],
        }


def test_migrations_are_at_head(postgres_session: Session) -> None:
    context = MigrationContext.configure(postgres_session.connection())
    assert context.get_current_revision() == EXPECTED_REVISION


def test_relations_reference_transaction_and_uniqueness(
    postgres_session: Session,
) -> None:
    administrator = Administrator(
        full_name="Administrateur PostgreSQL",
        email=f"postgres-{uuid4().hex}@example.test",
        password_hash="not-used-in-this-integration-test",
        is_active=True,
    )
    company = Company(name=f"Entreprise PostgreSQL {uuid4().hex}")
    contact = CompanyContact(company=company, full_name="Contact PostgreSQL", is_primary=True)
    postgres_session.add_all([administrator, company, contact])
    postgres_session.flush()

    repository = TrainingCaseRepository(postgres_session)
    reference = repository.next_reference(2099)
    training_case = TrainingCase(
        reference=reference,
        company_id=company.id,
        primary_contact_id=contact.id,
        theme="Stabilisation PostgreSQL",
        created_by=administrator.id,
    )
    repository.add(training_case)
    postgres_session.flush()
    postgres_session.expire_all()

    persisted = postgres_session.scalar(
        select(TrainingCase).where(TrainingCase.id == training_case.id)
    )
    assert persisted is not None
    assert persisted.company.name == company.name
    assert persisted.primary_contact is not None
    assert persisted.primary_contact.full_name == contact.full_name
    assert reference.startswith("TR-2099-")

    duplicate = TrainingCase(
        reference=reference,
        company_id=company.id,
        theme="Référence dupliquée",
        created_by=administrator.id,
    )
    postgres_session.add(duplicate)
    with pytest.raises(IntegrityError):
        postgres_session.flush()
    postgres_session.rollback()

    transient_name = f"Transaction annulée {uuid4().hex}"
    postgres_session.add(Company(name=transient_name))
    postgres_session.flush()
    postgres_session.rollback()
    assert postgres_session.scalar(select(Company).where(Company.name == transient_name)) is None


def test_document_generation_on_postgresql(
    postgres_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    administrator = Administrator(
        full_name="Administrateur Documents PostgreSQL",
        email=f"documents-{uuid4().hex}@example.test",
        password_hash="not-used-in-this-integration-test",
        is_active=True,
    )
    postgres_session.add(administrator)
    postgres_session.flush()
    training_case = make_ready_case(postgres_session, administrator)
    monkeypatch.setattr(settings, "document_storage_path", tmp_path)

    service = TrainingDocumentService(postgres_session, DocumentStorage(tmp_path))
    service.initialize(training_case.id, administrator.id)
    result = service.generate_all(training_case.id, administrator.id)

    assert result.all_generated is True
    assert len(result.results) == 5
    assert all(item.success for item in result.results)
    assert all(
        document.status == DocumentStatus.GENERATED.value
        for document in service.documents.list_by_case(training_case.id)
    )


def test_cv_pipeline_fallback_retry_and_human_validation_on_postgresql(
    postgres_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    administrator = Administrator(
        full_name="Administrateur CV PostgreSQL",
        email=f"cv-{uuid4().hex}@example.test",
        password_hash="not-used",
        is_active=True,
    )
    postgres_session.add(administrator)
    postgres_session.flush()
    monkeypatch.setattr(settings, "cv_storage_dir", tmp_path)
    stored = f"{uuid4()}.pdf"
    (tmp_path / stored).write_bytes(b"%PDF-integration")
    cv = TrainerCV(
        original_filename="integration.pdf",
        storage_filename=stored,
        mime_type="application/pdf",
        file_size=16,
        sha256=uuid4().hex.ljust(64, "0"),
    )
    postgres_session.add(cv)
    postgres_session.commit()

    failed = TrainerCVExtractionService(
        postgres_session, _PostgresLLM(True), _PostgresTextExtractor()
    ).extract(cv.id, administrator.id)
    assert failed.extraction_status == TrainerCVExtractionStatus.REVIEW_REQUIRED.value
    assert failed.extraction_error_code == "LLM_UNAVAILABLE"
    assert failed.raw_text
    assert (
        postgres_session.scalar(
            select(Trainer).where(Trainer.email == "karim@example.com")
        )
        is None
    )

    retried = TrainerCVExtractionService(
        postgres_session, _PostgresLLM(), _PostgresTextExtractor()
    ).extract(cv.id, administrator.id)
    assert retried.extraction_status == TrainerCVExtractionStatus.REVIEW_REQUIRED.value
    assert retried.extraction_error_code is None
    assert retried.parsed_json is not None

    trainer = CVService(postgres_session).validate(
        cv.id,
        TrainerCreate(full_name="Karim Test", email="karim@example.com"),
        administrator.id,
    )
    assert trainer.id == cv.trainer_id
    assert cv.extraction_status == TrainerCVExtractionStatus.VALIDATED.value
    assert postgres_session.scalar(
        select(Trainer).where(Trainer.email == "karim@example.com")
    ) is not None
