from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db_session
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


class SuccessfulSession:
    async def execute(self, statement: object) -> None:
        return None


class UnavailableSession:
    async def execute(self, statement: object) -> None:
        raise SQLAlchemyError("database unavailable")


async def override_successful_db_session() -> object:
    yield SuccessfulSession()


async def override_unavailable_db_session() -> object:
    yield UnavailableSession()


def test_readiness_returns_http_200_when_database_is_available() -> None:
    app.dependency_overrides[get_db_session] = override_successful_db_session

    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
    }


def test_readiness_returns_http_503_when_database_is_unavailable() -> None:
    app.dependency_overrides[get_db_session] = override_unavailable_db_session

    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "unavailable",
    }
