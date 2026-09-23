from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.administrator import Administrator
from app.models.company import Company, CompanyContact
from app.models.trainer import Trainer
from app.models.training_case import ActivityLog, TrainingCase, TrainingCaseStatus
from app.models.training_document import DocumentStatus, DocumentType, TrainingDocument
from app.models.training_need import TrainingNeed
from app.models.training_pricing import TrainingPricing
from app.models.training_program import (
    TrainingProgram,
    TrainingProgramDay,
    TrainingProgramItem,
    TrainingProgramItemMethod,
)
from app.services.training_document import TrainingDocumentService
from app.storage.documents import DocumentStorage


def login(client: TestClient, administrator: Administrator) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": administrator.email, "password": "Admin123!"},
    )
    assert response.status_code == 200


def make_ready_case(
    session: Session,
    administrator: Administrator,
    *,
    status: TrainingCaseStatus = TrainingCaseStatus.TARIFICATION_VALIDEE,
    vat_rate: Decimal = Decimal("19.000"),
) -> TrainingCase:
    company = Company(name=f"Entreprise École {uuid4()}")
    contact = CompanyContact(company=company, full_name="Amélie Ben Salah")
    trainer = Trainer(full_name="Noël Formateur")
    training_case = TrainingCase(
        reference=f"TR-2026-{str(uuid4().int)[:6]}",
        company=company,
        primary_contact=contact,
        trainer=trainer,
        theme="Audit des ressources humaines",
        description="Formation professionnelle structurée.",
        status=status.value,
        created_by=administrator.id,
    )
    training_case.training_need = TrainingNeed(
        target_audience="Responsables RH",
        location="Tunis",
        participant_count=12,
        duration_hours=Decimal("6.00"),
        objectives="Conduire un audit.",
        is_validated=True,
    )
    program = TrainingProgram(
        training_case=training_case,
        title="Programme d’audit RH",
        general_objectives="Maîtriser les étapes de l’audit.",
        evaluation_method="Étude de cas finale et restitution.",
        is_submitted=True,
        is_validated=True,
    )
    day = TrainingProgramDay(program=program, title="Jour 1 — Audit", position=1)
    module = TrainingProgramItem(
        day=day,
        item_type="MODULE",
        title="Définition de l’audit",
        content="Concepts, objectifs et méthodes.",
        theory_minutes=180,
        practice_minutes=180,
        position=1,
        method_links=[TrainingProgramItemMethod(method="ETUDE_DE_CAS")],
    )
    session.add(module)
    training_case.training_pricing = TrainingPricing(
        currency="TND",
        trainer_cost=Decimal("1000.000"),
        transport_cost=Decimal("100.000"),
        room_cost=Decimal("100.000"),
        meal_cost=Decimal("0.000"),
        other_cost=Decimal("0.000"),
        margin_rate=Decimal("20.000"),
        vat_rate=vat_rate,
        vat_exemption_reason="Exonération vérifiée" if vat_rate == 0 else None,
        program_day_count_snapshot=1,
        program_duration_minutes_snapshot=360,
        trainer_cost_initialization_method="DAILY_RATE",
        is_submitted=True,
        is_validated=True,
    )
    session.add(training_case)
    session.commit()
    session.refresh(training_case)
    return training_case


def test_initialization_requires_validated_pricing_and_is_idempotent(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    invalid = make_ready_case(
        db_session,
        active_administrator,
        status=TrainingCaseStatus.TARIFICATION_A_VALIDER,
    )
    valid = make_ready_case(db_session, active_administrator)
    login(client, active_administrator)

    assert client.post(f"/api/training-cases/{invalid.id}/documents/initialize").status_code == 409
    first = client.post(f"/api/training-cases/{valid.id}/documents/initialize")
    second = client.post(f"/api/training-cases/{valid.id}/documents/initialize")
    assert first.status_code == 200
    assert len(first.json()) == 5
    assert {item["status"] for item in first.json()} == {"PENDING"}
    assert len(second.json()) == 5
    assert db_session.query(TrainingDocument).filter_by(training_case_id=valid.id).count() == 5
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, valid.id)
    assert persisted_case is not None
    assert persisted_case.status == "DOCUMENTS_A_GENERER"


def test_generate_all_creates_valid_pdfs_and_advances_workflow(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "document_storage_path", tmp_path)
    training_case = make_ready_case(db_session, active_administrator)
    login(client, active_administrator)

    response = client.post(f"/api/training-cases/{training_case.id}/documents/generate-all")
    assert response.status_code == 200, response.text
    assert response.json()["all_generated"] is True
    documents = list(
        db_session.scalars(
            select(TrainingDocument).where(TrainingDocument.training_case_id == training_case.id)
        )
    )
    assert len(documents) == 5
    for document in documents:
        assert document.status == DocumentStatus.GENERATED.value
        assert document.mime_type == "application/pdf"
        assert document.sha256 and len(document.sha256) == 64
        assert document.snapshot_data
        assert "relative_path" not in document.snapshot_data
        assert document.relative_path is not None
        path = tmp_path / document.relative_path
        assert path.read_bytes().startswith(b"%PDF")
        assert len(PdfReader(path).pages) >= 1
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, training_case.id)
    assert persisted_case is not None
    assert persisted_case.status == "DOCUMENTS_GENERES"


def test_quote_hides_internal_costs_and_formats_zero_vat(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "document_storage_path", tmp_path)
    training_case = make_ready_case(db_session, active_administrator, vat_rate=Decimal("0.000"))
    login(client, active_administrator)
    response = client.post(f"/api/training-cases/{training_case.id}/documents/QUOTE/generate")
    assert response.status_code == 200, response.text
    document = db_session.scalar(
        select(TrainingDocument).where(
            TrainingDocument.training_case_id == training_case.id,
            TrainingDocument.document_type == "QUOTE",
        )
    )
    assert document is not None
    assert document.relative_path is not None
    text = "\n".join(
        page.extract_text() or "" for page in PdfReader(tmp_path / document.relative_path).pages
    )
    assert "0,000 %" in text
    assert "Exonération vérifiée" in text
    assert "Coût formateur" not in text
    assert "Marge" not in text


def test_download_and_readonly_after_close(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "document_storage_path", tmp_path)
    training_case = make_ready_case(db_session, active_administrator)
    login(client, active_administrator)
    missing = client.get(f"/api/training-cases/{training_case.id}/documents/PROGRAM/download")
    assert missing.status_code == 404
    assert (
        client.post(
            f"/api/training-cases/{training_case.id}/documents/PROGRAM/generate"
        ).status_code
        == 200
    )
    download = client.get(f"/api/training-cases/{training_case.id}/documents/PROGRAM/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert "attachment" in download.headers["content-disposition"]

    client.post(f"/api/training-cases/{training_case.id}/documents/generate-all")
    assert client.post(f"/api/training-cases/{training_case.id}/close").status_code == 200
    assert (
        client.post(
            f"/api/training-cases/{training_case.id}/documents/PROGRAM/generate"
        ).status_code
        == 409
    )
    assert (
        client.get(f"/api/training-cases/{training_case.id}/documents/PROGRAM/download").status_code
        == 200
    )
    actions = set(
        db_session.scalars(
            select(ActivityLog.action).where(ActivityLog.training_case_id == training_case.id)
        )
    )
    assert {
        "DocumentsInitialized",
        "TrainingDocumentGenerated",
        "TrainingDocumentDownloaded",
    } <= actions


def test_partial_failure_can_be_retried_without_losing_successes(
    db_session: Session,
    active_administrator: Administrator,
    tmp_path: Path,
    monkeypatch,
) -> None:
    training_case = make_ready_case(db_session, active_administrator)
    service = TrainingDocumentService(db_session, DocumentStorage(tmp_path))
    from app.services import training_document as service_module

    real_renderer = service_module.render_document

    def failing_renderer(document_type, snapshot):
        if document_type == "AGREEMENT":
            raise RuntimeError("forced renderer failure")
        return real_renderer(document_type, snapshot)

    monkeypatch.setattr(service_module, "render_document", failing_renderer)
    result = service.generate_all(training_case.id, active_administrator.id)
    assert result.all_generated is False
    assert sum(item.success for item in result.results) == 4
    failed_document = service.documents.get(training_case.id, DocumentType.AGREEMENT)
    assert failed_document is not None
    assert failed_document.status == "FAILED"
    persisted_case = db_session.get(TrainingCase, training_case.id)
    assert persisted_case is not None
    assert persisted_case.status == "DOCUMENTS_A_GENERER"

    monkeypatch.setattr(service_module, "render_document", real_renderer)
    retried = service.generate(training_case.id, DocumentType.AGREEMENT, active_administrator.id)
    assert retried.status == "GENERATED"
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, training_case.id)
    assert persisted_case is not None
    assert persisted_case.status == "DOCUMENTS_GENERES"
