import os
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from app.core.config import settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = BACKEND_ROOT.parent / "database" / "mysql-init" / "001-schema.sql"


def _test_database_url() -> str:
    url = os.getenv("MYSQL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("MYSQL_TEST_DATABASE_URL n'est pas configurée.")
    database = make_url(url).database or ""
    if not database.endswith("_test"):
        pytest.fail("La base MySQL d'intégration doit se terminer par '_test'.")
    return url


@pytest.fixture(scope="session")
def mysql_engine() -> Generator[Engine, None, None]:
    url = _test_database_url()
    previous_url = os.environ.get("DATABASE_URL")
    previous_settings_url = settings.database_url
    os.environ["DATABASE_URL"] = url
    settings.database_url = url
    engine = create_engine(url, pool_pre_ping=True)
    raw = engine.raw_connection()
    try:
        cursor = raw.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        cursor.execute("SHOW TABLES")
        for (table_name,) in cursor.fetchall():
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
            if statement.strip():
                cursor.execute(statement)
        raw.commit()
    finally:
        raw.close()
    try:
        yield engine
    finally:
        engine.dispose()
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        settings.database_url = previous_settings_url


@pytest.fixture()
def mysql_session(mysql_engine: Engine) -> Generator[Session, None, None]:
    with mysql_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, expire_on_commit=False)
        try:
            yield session
        finally:
            session.close()
            if transaction.is_active:
                transaction.rollback()
