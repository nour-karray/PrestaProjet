from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.administrator import Administrator

test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def active_administrator(db_session: Session) -> Administrator:
    administrator = Administrator(
        full_name="Administrateur Test",
        email="admin@test.local",
password_hash=hash_password("TestOnly-StrongPassword!42"),
        is_active=True,
    )
    db_session.add(administrator)
    db_session.commit()
    db_session.refresh(administrator)
    return administrator


@pytest.fixture
def inactive_administrator(db_session: Session) -> Administrator:
    administrator = Administrator(
        full_name="Compte Inactif",
        email="inactive@test.local",
        password_hash=hash_password("TestOnly-StrongPassword!42"),
        is_active=False,
    )
    db_session.add(administrator)
    db_session.commit()
    db_session.refresh(administrator)
    return administrator
