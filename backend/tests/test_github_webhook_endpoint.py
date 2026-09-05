import json
import logging
from dataclasses import dataclass
from typing import Any

from fastapi.testclient import TestClient
import pytest

from app.api.v1.endpoints.webhooks import get_webhook_ingestion_service
from app.core.config import settings
from app.models import WebhookEventStatus
from app.main import app
from app.services.github.webhook_ingestion import WebhookIngestionResult, WebhookPersistenceError
from app.services.github.webhook_security import calculate_signature

SECRET = "unit-test-webhook-secret"
DELIVERY_ID = "11111111-1111-4111-8111-111111111111"


@dataclass
class IngestionCall:
    delivery_id: str
    event_name: str
    payload: dict[str, object]
    raw_body: bytes


class FakeIngestionService:
    def __init__(
        self,
        *,
        duplicate: bool = False,
        fail: bool = False,
    ) -> None:
        self.duplicate = duplicate
        self.fail = fail
        self.calls: list[IngestionCall] = []

    async def ingest(
        self,
        *,
        delivery_id: str,
        event_name: str,
        payload: dict[str, object],
        raw_body: bytes,
    ) -> WebhookIngestionResult:
        self.calls.append(
            IngestionCall(
                delivery_id=delivery_id,
                event_name=event_name,
                payload=payload,
                raw_body=raw_body,
            )
        )
        if self.fail:
            raise WebhookPersistenceError("failed")

        action = payload.get("action")
        normalized_action = action if isinstance(action, str) else None
        if event_name == "pull_request" and normalized_action in {"opened", "synchronize", "reopened", "closed"}:
            event_status = WebhookEventStatus.RECEIVED
        else:
            event_status = WebhookEventStatus.IGNORED

        return WebhookIngestionResult(
            delivery_id=delivery_id,
            event=event_name,
            action=normalized_action,
            status=event_status,
            duplicate=self.duplicate,
        )


@pytest.fixture(autouse=True)
def configure_webhook_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "github_webhook_secret", SECRET)
    monkeypatch.setattr(settings, "github_webhook_max_body_bytes", 2 * 1024 * 1024)
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def encode_payload(payload: Any) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def webhook_headers(
    body: bytes,
    *,
    event: str = "ping",
    delivery_id: str = DELIVERY_ID,
    secret: str = SECRET,
    signature: str | None = None,
    content_type: str = "application/json",
) -> dict[str, str]:
    return {
        "X-Hub-Signature-256": signature or calculate_signature(secret, body),
        "X-GitHub-Event": event,
        "X-GitHub-Delivery": delivery_id,
        "Content-Type": content_type,
    }


def override_service(service: FakeIngestionService) -> None:
    app.dependency_overrides[get_webhook_ingestion_service] = lambda: service


def test_missing_signature_is_rejected(client: TestClient) -> None:
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body)
    headers.pop("X-Hub-Signature-256")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 401


def test_invalid_signature_is_rejected(client: TestClient) -> None:
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body, signature="sha256=" + ("0" * 64))

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 401


def test_missing_event_header_is_rejected(client: TestClient) -> None:
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body)
    headers.pop("X-GitHub-Event")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 400


def test_missing_delivery_header_is_rejected(client: TestClient) -> None:
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body)
    headers.pop("X-GitHub-Delivery")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 400


def test_malformed_delivery_header_is_rejected(client: TestClient) -> None:
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body, delivery_id="not-a-delivery-id")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 400


def test_invalid_json_is_rejected_after_valid_signature(client: TestClient) -> None:
    body = b"{invalid-json"
    headers = webhook_headers(body)

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 400


def test_non_object_json_is_rejected(client: TestClient) -> None:
    body = encode_payload(["not", "an", "object"])
    headers = webhook_headers(body)

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 400


def test_unsupported_content_type_is_rejected(client: TestClient) -> None:
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body, content_type="text/plain")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 415


def test_json_content_type_allows_charset_parameter(client: TestClient) -> None:
    service = FakeIngestionService()
    override_service(service)
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body, content_type="application/json; charset=utf-8")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 200


def test_oversized_content_length_is_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "github_webhook_max_body_bytes", 5)
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body)
    headers["Content-Length"] = "999"

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 413


def test_oversized_actual_body_is_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "github_webhook_max_body_bytes", 5)
    body = b"123456"
    headers = webhook_headers(body)
    headers.pop("Content-Length", None)

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 413


def test_valid_ping_returns_pong_and_requests_persistence(client: TestClient) -> None:
    service = FakeIngestionService()
    override_service(service)
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body, event="ping")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "pong",
        "delivery_id": DELIVERY_ID,
        "event": "ping",
    }
    assert service.calls[0] == IngestionCall(
        delivery_id=DELIVERY_ID,
        event_name="ping",
        payload={"zen": "hello"},
        raw_body=body,
    )


def test_supported_pull_request_action_returns_accepted(client: TestClient) -> None:
    service = FakeIngestionService()
    override_service(service)
    body = encode_payload({"action": "opened", "number": 1, "repository": {"id": 2}})
    headers = webhook_headers(body, event="pull_request")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 202
    assert response.json() == {
        "status": "accepted",
        "delivery_id": DELIVERY_ID,
        "event": "pull_request",
        "action": "opened",
    }


def test_unsupported_pull_request_action_returns_ignored(client: TestClient) -> None:
    service = FakeIngestionService()
    override_service(service)
    body = encode_payload({"action": "edited", "number": 1, "repository": {"id": 2}})
    headers = webhook_headers(body, event="pull_request")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 202
    assert response.json() == {
        "status": "ignored",
        "delivery_id": DELIVERY_ID,
        "event": "pull_request",
        "action": "edited",
    }


def test_unsupported_event_returns_ignored(client: TestClient) -> None:
    service = FakeIngestionService()
    override_service(service)
    body = encode_payload({"action": "created"})
    headers = webhook_headers(body, event="issues")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 202
    assert response.json() == {
        "status": "ignored",
        "delivery_id": DELIVERY_ID,
        "event": "issues",
        "action": "created",
    }


def test_duplicate_delivery_returns_duplicate(client: TestClient) -> None:
    service = FakeIngestionService(duplicate=True)
    override_service(service)
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body, event="ping")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "duplicate",
        "delivery_id": DELIVERY_ID,
        "event": "ping",
    }


def test_database_failure_returns_safe_response(client: TestClient) -> None:
    service = FakeIngestionService(fail=True)
    override_service(service)
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body, event="ping")

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service unavailable."}


def test_missing_webhook_secret_returns_service_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "github_webhook_secret", "")
    body = encode_payload({"zen": "hello"})
    headers = webhook_headers(body)

    response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service unavailable."}


def test_logs_do_not_include_secret_or_payload(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    service = FakeIngestionService()
    override_service(service)
    body = encode_payload({"zen": "very-secret-payload-marker"})
    headers = webhook_headers(body, event="ping")

    with caplog.at_level(logging.INFO):
        response = client.post("/api/v1/webhooks/github", content=body, headers=headers)

    logs = caplog.text
    assert response.status_code == 200
    assert SECRET not in logs
    assert "very-secret-payload-marker" not in logs
    assert headers["X-Hub-Signature-256"] not in logs
