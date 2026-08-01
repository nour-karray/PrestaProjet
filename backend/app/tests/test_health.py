from fastapi.testclient import TestClient

from app.ai.local_llm import LLMHealth, OllamaLocalLLMClient
from app.models.administrator import Administrator


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_allows_frontend_origin(client: TestClient) -> None:
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_ai_health_is_protected(client: TestClient) -> None:
    assert client.get("/api/v1/ai/health").status_code == 401


def test_ai_health_reports_ollama_without_secrets(
    client: TestClient,
    active_administrator: Administrator,
    monkeypatch,
) -> None:
    client.post(
        "/api/auth/login",
        json={"email": active_administrator.email, "password": "Admin123!"},
    )
    monkeypatch.setattr(
        OllamaLocalLLMClient,
        "health",
        lambda _: LLMHealth("available", "ollama", "qwen-test", 12, None),
    )
    response = client.get("/api/v1/ai/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "available",
        "provider": "ollama",
        "model": "qwen-test",
        "model_available": True,
        "latency_ms": 12,
        "reason": None,
    }
