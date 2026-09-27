from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.administrator import Administrator


def login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
json={"email": "admin@test.local", "password": "TestOnly-StrongPassword!42"},
    )
    assert response.status_code == 200


def test_login_sets_http_only_cookies(
    client: TestClient,
    active_administrator: Administrator,
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": active_administrator.email, "password": "TestOnly-StrongPassword!42"},
    )

    assert response.status_code == 200
    assert response.json()["administrator"]["email"] == active_administrator.email
    assert response.json()["message"] == "Connexion réussie."
    cookies = response.headers.get_list("set-cookie")
    assert any("access_token=" in cookie and "HttpOnly" in cookie for cookie in cookies)
    assert any("refresh_token=" in cookie and "HttpOnly" in cookie for cookie in cookies)


def test_login_rejects_invalid_credentials(
    client: TestClient,
    active_administrator: Administrator,
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": active_administrator.email, "password": "Wrong123!"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_inactive_administrator(
    client: TestClient,
    inactive_administrator: Administrator,
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": inactive_administrator.email, "password": "TestOnly-StrongPassword!42"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "INACTIVE_ACCOUNT"


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_me_returns_current_administrator(
    client: TestClient,
    active_administrator: Administrator,
) -> None:
    login(client)

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(active_administrator.id)


def test_refresh_rotates_tokens(
    client: TestClient,
    active_administrator: Administrator,
) -> None:
    login(client)

    response = client.post("/api/auth/refresh")

    assert response.status_code == 200
    assert response.json()["message"] == "Session renouvelée."
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_logout_clears_authentication(
    client: TestClient,
    active_administrator: Administrator,
) -> None:
    login(client)

    response = client.post("/api/auth/logout")
    protected_response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert protected_response.status_code == 401


def test_expired_access_token_is_rejected(
    client: TestClient,
    active_administrator: Administrator,
) -> None:
    expired_token = jwt.encode(
        {
            "sub": str(active_administrator.id),
            "type": "access",
            "iat": datetime.now(UTC) - timedelta(minutes=2),
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    client.cookies.set("access_token", expired_token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "TOKEN_EXPIRED"


def test_invalid_access_token_is_rejected(client: TestClient) -> None:
    client.cookies.set("access_token", "invalid-token")

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"
