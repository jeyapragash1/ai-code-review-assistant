from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_http_200() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_health_returns_complete_json_response() -> None:
    response = client.get("/api/v1/health")

    assert response.json() == {
        "status": "healthy",
        "service": "ai-code-review-assistant-api",
        "version": "0.1.0",
        "environment": "development",
    }


def test_health_returns_json_content_type() -> None:
    response = client.get("/api/v1/health")

    assert response.headers["content-type"].startswith("application/json")
