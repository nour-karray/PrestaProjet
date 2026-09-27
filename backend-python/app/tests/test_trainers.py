import zipfile
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.administrator import Administrator
from app.models.company import Company
from app.models.trainer import TrainerCV, TrainerCVExtractionStatus
from app.models.training_case import ActivityLog, TrainingCase

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def make_docx(text: str = "CV de test") -> bytes:
    content = BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr(
            "word/document.xml",
            f"<document><body><p>{text}</p></body></document>",
        )
    return content.getvalue()


def login(client: TestClient, administrator: Administrator) -> None:
    response = client.post(
        "/api/auth/login",
json={"email": administrator.email, "password": "TestOnly-StrongPassword!42"},
    )
    assert response.status_code == 200


def create_trainer(client: TestClient, name: str = "Karim Ben Salah") -> dict:
    response = client.post(
        "/api/trainers",
        json={
            "full_name": f"  {name}  ",
            "email": "KARIM@EXAMPLE.COM",
            "job_title": "Marketing digital",
            "years_experience": 8,
            "notes": "",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_trainer_crud_archive_and_normalization(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    login(client, active_administrator)
    trainer = create_trainer(client)
    assert trainer["full_name"] == "Karim Ben Salah"
    assert trainer["email"] == "karim@example.com"
    assert trainer["notes"] is None

    listed = client.get("/api/trainers", params={"search": "Marketing"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    audit_trainer = client.post(
        "/api/trainers",
        json={"full_name": "Sonia Audit", "job_title": "Consultante Audit RH"},
    )
    assert audit_trainer.status_code == 201
    specialized = client.get("/api/trainers", params={"specialty": "Audit RH"})
    assert specialized.status_code == 200
    assert specialized.json()["total"] == 1
    assert specialized.json()["items"][0]["full_name"] == "Sonia Audit"
    narrowed = client.get(
        "/api/trainers", params={"specialty": "Audit RH", "search": "Karim"}
    )
    assert narrowed.status_code == 200
    assert narrowed.json()["total"] == 0

    updated = client.patch(f"/api/trainers/{trainer['id']}", json={"city": " Tunis "})
    assert updated.status_code == 200
    assert updated.json()["city"] == "Tunis"
    invalid = client.patch(f"/api/trainers/{trainer['id']}", json={"full_name": ""})
    assert invalid.status_code == 422

    archived = client.delete(f"/api/trainers/{trainer['id']}")
    assert archived.status_code == 200
    assert archived.json()["is_active"] is False
    assert client.get("/api/trainers").json()["total"] == 1
    actions = list(db_session.scalars(select(ActivityLog.action)))
    assert "TrainerCreated" in actions
    assert "TrainerArchived" in actions


def test_cv_upload_duplicate_list_and_delete(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(settings, "cv_storage_dir", tmp_path / "cv")
    login(client, active_administrator)
    content = make_docx()
    upload = client.post(
        "/api/trainer-cvs/upload",
        files={"file": ("cv-formateur.docx", BytesIO(content), DOCX_MIME)},
    )
    assert upload.status_code == 201
    stored_name = next((tmp_path / "cv").iterdir()).name
    assert stored_name != "cv-formateur.docx"
    assert Path(stored_name).suffix == ".docx"

    duplicate = client.post(
        "/api/trainer-cvs/upload",
        files={"file": ("copie.docx", BytesIO(content), DOCX_MIME)},
    )
    assert duplicate.status_code == 409
    assert len(list((tmp_path / "cv").iterdir())) == 1

    listed = client.get("/api/trainer-cvs")
    assert listed.status_code == 200
    assert "raw_text" not in listed.json()["items"][0]

    deleted = client.delete(f"/api/trainer-cvs/{upload.json()['id']}")
    assert deleted.status_code == 204
    assert list((tmp_path / "cv").iterdir()) == []
    actions = list(db_session.scalars(select(ActivityLog.action)))
    assert "CVUploaded" in actions
    assert "CVDeleted" in actions


@pytest.mark.parametrize(
    ("filename", "mime_type", "content", "expected_code"),
    [
        ("cv.txt", "text/plain", b"texte", "FILE_INVALID"),
        ("cv.pdf.exe", "application/pdf", b"%PDF-", "INVALID_CV_FILENAME"),
        ("../cv.pdf", "application/pdf", b"%PDF-", "INVALID_CV_FILENAME"),
        ("cv.pdf", "application/pdf", b"not a pdf", "FILE_INVALID"),
        ("cv.docx", DOCX_MIME, b"PK\x03\x04invalid", "FILE_INVALID"),
    ],
)
def test_cv_upload_security_validation(
    client: TestClient,
    active_administrator: Administrator,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    filename: str,
    mime_type: str,
    content: bytes,
    expected_code: str,
) -> None:
    monkeypatch.setattr(settings, "cv_storage_dir", tmp_path / "cv")
    login(client, active_administrator)
    response = client.post(
        "/api/trainer-cvs/upload",
        files={"file": (filename, BytesIO(content), mime_type)},
    )
    assert response.status_code == 422
    assert response.json()["code"] == expected_code


def test_assignment_and_unassignment_are_logged(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    company = Company(name="Entreprise Test")
    db_session.add(company)
    db_session.flush()
    training_case = TrainingCase(
        reference="TR-2026-000999",
        company_id=company.id,
        theme="Audit",
        created_by=active_administrator.id,
    )
    db_session.add(training_case)
    db_session.commit()
    login(client, active_administrator)
    trainer = create_trainer(client, "Nom vérifié")

    assigned = client.post(
        f"/api/training-cases/{training_case.id}/trainer",
        json={"trainer_id": trainer["id"]},
    )
    assert assigned.status_code == 200
    assert assigned.json()["trainer"]["full_name"] == "Nom vérifié"
    unassigned = client.post(
        f"/api/training-cases/{training_case.id}/trainer",
        json={"trainer_id": None},
    )
    assert unassigned.status_code == 200
    assert unassigned.json()["trainer"] is None
    actions = list(db_session.scalars(select(ActivityLog.action)))
    assert "TrainerAssigned" in actions
    assert "TrainerUnassigned" in actions


def test_private_trainer_route_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/trainers").status_code == 401
    assert client.post(f"/api/trainer-cvs/{uuid4()}/extract").status_code == 401


def test_completed_cv_requires_human_validation(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    cv = TrainerCV(
        original_filename="cv.pdf",
        storage_filename=f"{uuid4()}.pdf",
        mime_type="application/pdf",
        file_size=100,
        sha256=uuid4().hex.ljust(64, "0"),
        extraction_status=TrainerCVExtractionStatus.REVIEW_REQUIRED.value,
        parsed_json={"full_name": "Valeur non approuvée"},
    )
    db_session.add(cv)
    db_session.commit()
    login(client, active_administrator)
    response = client.post(
        f"/api/trainer-cvs/{cv.id}/validate",
        json={"full_name": "Valeur corrigée", "email": "CORRIGE@EXAMPLE.COM"},
    )
    assert response.status_code == 201
    assert response.json()["full_name"] == "Valeur corrigée"
    assert response.json()["email"] == "corrige@example.com"
    db_session.refresh(cv)
    assert cv.extraction_status == TrainerCVExtractionStatus.VALIDATED.value
    assert str(cv.trainer_id) == response.json()["id"]
    repeated = client.post(
        f"/api/trainer-cvs/{cv.id}/validate",
        json={"full_name": "Nouvelle valeur"},
    )
    assert repeated.status_code == 409


def test_validated_trainer_exposes_and_opens_original_cv(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(settings, "cv_storage_dir", tmp_path / "cv")
    login(client, active_administrator)
    content = make_docx("CV AMIRA BOUZID")
    upload = client.post(
        "/api/trainer-cvs/upload",
        files={"file": ("amira-bouzid.docx", BytesIO(content), DOCX_MIME)},
    )
    assert upload.status_code == 201
    cv = db_session.get(TrainerCV, UUID(upload.json()["id"]))
    assert cv is not None
    cv.extraction_status = TrainerCVExtractionStatus.REVIEW_REQUIRED.value
    db_session.commit()

    validated = client.post(
        f"/api/trainer-cvs/{upload.json()['id']}/validate",
        json={"full_name": "AMIRA BOUZID"},
    )
    assert validated.status_code == 201
    trainer_id = validated.json()["id"]
    assert validated.json()["cv_id"] == upload.json()["id"]

    opened = client.get(f"/api/trainers/{trainer_id}/cv")
    assert opened.status_code == 200
    assert opened.content == content
    assert opened.headers["content-type"] == DOCX_MIME
    assert "inline" in opened.headers["content-disposition"]
