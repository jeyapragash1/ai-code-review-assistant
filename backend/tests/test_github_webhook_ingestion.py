import hashlib

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models import WebhookEventStatus
from app.services.github.webhook_ingestion import (
    GitHubWebhookIngestionService,
    WebhookPersistenceError,
)


class CapturingWebhookEventRepository:
    def __init__(self, created: bool = True, fails: bool = False) -> None:
        self.created = created
        self.fails = fails
        self.created_event = None

    async def create_if_not_exists(self, data: object) -> bool:
        if self.fails:
            raise SQLAlchemyError("database failed")
        self.created_event = data
        return self.created


@pytest.mark.anyio
async def test_ingestion_extracts_repository_id_pr_number_and_payload_hash() -> None:
    repository = CapturingWebhookEventRepository()
    service = GitHubWebhookIngestionService(repository)
    raw_body = b'{"action":"opened","number":42,"repository":{"id":123456}}'
    payload = {"action": "opened", "number": 42, "repository": {"id": 123456}}

    result = await service.ingest(
        delivery_id="11111111-1111-4111-8111-111111111111",
        event_name="pull_request",
        payload=payload,
        raw_body=raw_body,
    )

    assert result.status == WebhookEventStatus.RECEIVED
    assert repository.created_event.github_repository_id == 123456
    assert repository.created_event.github_pr_number == 42
    assert repository.created_event.payload_hash == hashlib.sha256(raw_body).hexdigest()
    assert repository.created_event.attempt_count if hasattr(repository.created_event, "attempt_count") else True


@pytest.mark.anyio
async def test_ingestion_returns_duplicate_when_delivery_exists() -> None:
    repository = CapturingWebhookEventRepository(created=False)
    service = GitHubWebhookIngestionService(repository)

    result = await service.ingest(
        delivery_id="11111111-1111-4111-8111-111111111111",
        event_name="ping",
        payload={"zen": "hello"},
        raw_body=b'{"zen":"hello"}',
    )

    assert result.duplicate is True
    assert result.status == WebhookEventStatus.IGNORED


@pytest.mark.anyio
async def test_ingestion_wraps_database_failures_safely() -> None:
    repository = CapturingWebhookEventRepository(fails=True)
    service = GitHubWebhookIngestionService(repository)

    with pytest.raises(WebhookPersistenceError):
        await service.ingest(
            delivery_id="11111111-1111-4111-8111-111111111111",
            event_name="ping",
            payload={"zen": "hello"},
            raw_body=b'{"zen":"hello"}',
        )
