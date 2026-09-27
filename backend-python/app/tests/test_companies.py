from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.administrator import Administrator
from app.models.company import Company


def login(client: TestClient, administrator: Administrator) -> None:
    response = client.post(
        "/api/auth/login",
json={"email": administrator.email, "password": "TestOnly-StrongPassword!42"},
    )
    assert response.status_code == 200


def create_company(client: TestClient, name: str = "  Alpha   Conseil  ") -> dict:
    response = client.post(
        "/api/companies",
        json={"name": name, "city": "Tunis", "country": "Tunisie"},
    )
    assert response.status_code == 201
    return response.json()


def test_companies_require_authentication(client: TestClient) -> None:
    assert client.get("/api/companies").status_code == 401


def test_create_validate_and_reject_duplicate(
    client: TestClient, active_administrator: Administrator
) -> None:
    login(client, active_administrator)
    company = create_company(client)
    assert company["name"] == "Alpha Conseil"
    assert client.post("/api/companies", json={"name": "   "}).status_code == 422
    assert client.post("/api/companies", json={"name": "alpha conseil"}).status_code == 409


def test_list_search_and_get_company(
    client: TestClient, active_administrator: Administrator
) -> None:
    login(client, active_administrator)
    company = create_company(client)
    create_company(client, "Beta Industrie")

    listing = client.get("/api/companies", params={"search": "alpha"}).json()
    assert listing["total"] == 1
    assert listing["items"][0]["name"] == "Alpha Conseil"
    assert client.get(f"/api/companies/{company['id']}").status_code == 200
    assert client.get(f"/api/companies/{uuid4()}").status_code == 404


def test_update_archive_and_archive_filters(
    client: TestClient, active_administrator: Administrator
) -> None:
    login(client, active_administrator)
    company = create_company(client)
    updated = client.patch(f"/api/companies/{company['id']}", json={"city": "Sousse"})
    assert updated.json()["city"] == "Sousse"
    assert client.delete(f"/api/companies/{company['id']}").status_code == 200
    assert client.get("/api/companies").json()["total"] == 0
    archived = client.get("/api/companies", params={"include_archived": "true"}).json()
    assert archived["total"] == 1
    assert archived["items"][0]["is_archived"] is True


def test_contact_lifecycle_and_primary_replacement(
    client: TestClient, active_administrator: Administrator
) -> None:
    login(client, active_administrator)
    company = create_company(client)
    first = client.post(
        f"/api/companies/{company['id']}/contacts",
        json={
            "full_name": "Premier Contact",
            "email": "premier@formation.local",
            "is_primary": True,
        },
    ).json()
    second = client.post(
        f"/api/companies/{company['id']}/contacts",
        json={"full_name": "Second Contact"},
    ).json()
    updated = client.patch(
        f"/api/contacts/{second['id']}",
        json={"job_title": "Direction", "is_primary": True},
    )
    assert updated.status_code == 200
    contacts = client.get(f"/api/companies/{company['id']}/contacts").json()
    assert next(item for item in contacts if item["id"] == first["id"])["is_primary"] is False
    assert next(item for item in contacts if item["id"] == second["id"])["is_primary"] is True
    assert client.delete(f"/api/contacts/{first['id']}").status_code == 200
    assert len(client.get(f"/api/companies/{company['id']}/contacts").json()) == 1


def test_missing_company_and_contact(
    client: TestClient, active_administrator: Administrator
) -> None:
    login(client, active_administrator)
    assert (
        client.post(f"/api/companies/{uuid4()}/contacts", json={"full_name": "Contact"}).status_code
        == 404
    )
    assert client.patch(f"/api/contacts/{uuid4()}", json={"full_name": "X"}).status_code == 404


def test_archiving_does_not_delete_company(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    login(client, active_administrator)
    company = create_company(client)
    client.delete(f"/api/companies/{company['id']}")
    assert db_session.get(Company, UUID(company["id"])) is not None
