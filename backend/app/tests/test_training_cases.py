from datetime import date
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.administrator import Administrator
from app.models.company import Company, CompanyContact
from app.models.training_case import TrainingCase, TrainingCaseStatus


def login(client: TestClient, administrator: Administrator) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": administrator.email, "password": "Admin123!"},
    )
    assert response.status_code == 200


def company_with_contact(
    session: Session, *, archived: bool = False, name: str = "Entreprise Test"
) -> tuple[Company, CompanyContact]:
    company = Company(name=name, is_archived=archived)
    contact = CompanyContact(full_name=f"Contact {name}")
    company.contacts.append(contact)
    session.add(company)
    session.commit()
    session.refresh(company)
    session.refresh(contact)
    return company, contact


def create_case(client: TestClient, company: Company, contact: CompanyContact) -> dict:
    response = client.post(
        "/api/training-cases",
        json={
            "company_id": str(company.id),
            "primary_contact_id": str(contact.id),
            "theme": "Audit des ressources humaines",
            "desired_start_date": "2026-09-01",
            "desired_end_date": "2026-09-03",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_training_cases_require_authentication(client: TestClient) -> None:
    assert client.get("/api/training-cases").status_code == 401


def test_creation_reference_uniqueness_and_activity(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    company, contact = company_with_contact(db_session)
    login(client, active_administrator)
    first = create_case(client, company, contact)
    second = create_case(client, company, contact)

    assert first["reference"].startswith("TR-")
    assert first["reference"] != second["reference"]
    assert int(second["reference"][-6:]) == int(first["reference"][-6:]) + 1
    activity = client.get(f"/api/training-cases/{first['id']}/activity").json()
    assert activity[0]["action"] == "CREATION"


def test_creation_validations(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    company, contact = company_with_contact(db_session)
    other_company, other_contact = company_with_contact(db_session, name="Autre Entreprise")
    archived, _ = company_with_contact(db_session, archived=True, name="Entreprise Archivée")
    login(client, active_administrator)

    assert (
        client.post(
            "/api/training-cases",
            json={"company_id": str(company.id), "theme": " "},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/training-cases",
            json={"company_id": str(uuid4()), "theme": "Formation"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/training-cases",
            json={"company_id": str(archived.id), "theme": "Formation"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/training-cases",
            json={
                "company_id": str(company.id),
                "primary_contact_id": str(other_contact.id),
                "theme": "Formation",
            },
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/training-cases",
            json={
                "company_id": str(other_company.id),
                "primary_contact_id": str(contact.id),
                "theme": "Formation",
            },
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/training-cases",
            json={
                "company_id": str(company.id),
                "theme": "Formation",
                "desired_start_date": "2026-09-03",
                "desired_end_date": "2026-09-01",
            },
        ).status_code
        == 422
    )


def test_list_search_filter_and_pagination(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    company, contact = company_with_contact(db_session)
    login(client, active_administrator)
    created = create_case(client, company, contact)
    create_case(client, company, contact)

    page = client.get("/api/training-cases", params={"page_size": 1}).json()
    assert page["total"] == 2
    assert len(page["items"]) == 1
    reference_result = client.get(
        "/api/training-cases", params={"reference": created["reference"]}
    ).json()
    assert reference_result["total"] == 1
    status_result = client.get("/api/training-cases", params={"status": "BROUILLON"}).json()
    assert status_result["total"] == 2


def test_update_and_status_transitions(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    company, contact = company_with_contact(db_session)
    login(client, active_administrator)
    created = create_case(client, company, contact)
    updated = client.patch(
        f"/api/training-cases/{created['id']}",
        json={"theme": "Nouveau thème"},
    )
    assert updated.json()["theme"] == "Nouveau thème"

    received = client.post(
        f"/api/training-cases/{created['id']}/change-status",
        json={"status": "DEMANDE_RECUE"},
    )
    assert received.json()["status"] == "DEMANDE_RECUE"
    searching = client.post(
        f"/api/training-cases/{created['id']}/change-status",
        json={"status": "RECHERCHE_FORMATEUR"},
    )
    assert searching.json()["status"] == "RECHERCHE_FORMATEUR"
    invalid = client.post(
        f"/api/training-cases/{created['id']}/change-status",
        json={"status": "PROGRAMME_VALIDE"},
    )
    assert invalid.status_code == 409


def test_cancel_archive_and_default_exclusion(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    company, contact = company_with_contact(db_session)
    login(client, active_administrator)
    created = create_case(client, company, contact)
    cancelled = client.post(f"/api/training-cases/{created['id']}/cancel")
    assert cancelled.json()["status"] == "ANNULE"
    archived = client.post(f"/api/training-cases/{created['id']}/archive")
    assert archived.json()["status"] == "ARCHIVE"
    assert archived.json()["is_archived"] is True
    assert client.get("/api/training-cases").json()["total"] == 0
    assert (
        client.get("/api/training-cases", params={"include_archived": "true"}).json()["total"] == 1
    )
    assert db_session.get(TrainingCase, UUID(created["id"])) is not None


def test_close_documents_generated_case(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    company, _ = company_with_contact(db_session)
    case = TrainingCase(
        reference="TR-2026-999999",
        company_id=company.id,
        theme="Dossier futur",
        status=TrainingCaseStatus.DOCUMENTS_GENERES.value,
        created_by=active_administrator.id,
        desired_start_date=date(2026, 9, 1),
    )
    db_session.add(case)
    db_session.commit()
    login(client, active_administrator)

    response = client.post(f"/api/training-cases/{case.id}/close")
    assert response.status_code == 200
    assert response.json()["status"] == "TERMINE"
    assert response.json()["closed_at"] is not None
