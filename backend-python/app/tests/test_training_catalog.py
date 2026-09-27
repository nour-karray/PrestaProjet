from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.administrator import Administrator
from app.models.training_catalog import TrainingCatalogItem


def test_catalog_exposes_only_active_items(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    active_item = TrainingCatalogItem(
        category="Intelligence artificielle",
        title="Intelligence artificielle",
        is_active=True,
    )
    db_session.add_all([
        active_item,
        TrainingCatalogItem(
            category="Intelligence artificielle",
            title="Formation archivée",
            is_active=False,
        ),
    ])
    db_session.commit()
    login = client.post(
        "/api/auth/login",
json={"email": active_administrator.email, "password": "TestOnly-StrongPassword!42"},
    )
    assert login.status_code == 200

    response = client.get("/api/training-catalog")

    assert response.status_code == 200
    assert response.json() == [{
        "id": str(active_item.id),
        "category": "Intelligence artificielle",
        "title": "Intelligence artificielle",
        "is_active": True,
    }]
