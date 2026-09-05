import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from sqlalchemy.exc import SQLAlchemyError

from app.models import WebhookEventStatus
from app.repositories.webhook_event import WebhookEventCreate, WebhookEventRepository

SUPPORTED_EVENTS: Final[set[str]] = {"ping", "pull_request"}
SUPPORTED_PULL_REQUEST_ACTIONS: Final[set[str]] = {
    "opened",
    "synchronize",
    "reopened",
    "closed",
}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookIngestionResult:
    delivery_id: str
    event: str
    action: str | None
    status: WebhookEventStatus
    duplicate: bool = False


class WebhookPersistenceError(Exception):
    pass


class GitHubWebhookIngestionService:
    def __init__(self, repository: WebhookEventRepository) -> None:
        self.repository = repository

    async def ingest(
        self,
        *,
        delivery_id: str,
        event_name: str,
        payload: dict[str, object],
        raw_body: bytes,
    ) -> WebhookIngestionResult:
        action = _extract_optional_string(payload, "action")
        status = determine_initial_status(event_name, action)
        payload_hash = hashlib.sha256(raw_body).hexdigest()

        event_data = WebhookEventCreate(
            github_delivery_id=delivery_id,
            event_name=event_name,
            action=action,
            github_repository_id=extract_repository_id(payload),
            github_pr_number=extract_pull_request_number(payload),
            payload=payload,
            payload_hash=payload_hash,
            status=status,
            received_at=datetime.now(UTC),
        )

        try:
            created = await self.repository.create_if_not_exists(event_data)
        except SQLAlchemyError as exc:
            raise WebhookPersistenceError("Webhook persistence failed.") from exc

        duplicate = not created
        logger.info(
            "Webhook delivery ingested.",
            extra={
                "delivery_id": delivery_id,
                "event": event_name,
                "action": action,
                "ingestion_status": "duplicate" if duplicate else status.value,
            },
        )

        return WebhookIngestionResult(
            delivery_id=delivery_id,
            event=event_name,
            action=action,
            status=status,
            duplicate=duplicate,
        )


def determine_initial_status(event_name: str, action: str | None) -> WebhookEventStatus:
    if event_name == "ping":
        return WebhookEventStatus.IGNORED
    if event_name == "pull_request" and action in SUPPORTED_PULL_REQUEST_ACTIONS:
        return WebhookEventStatus.RECEIVED
    return WebhookEventStatus.IGNORED


def extract_repository_id(payload: dict[str, object]) -> int | None:
    repository = payload.get("repository")
    if not isinstance(repository, dict):
        return None

    repository_id = repository.get("id")
    if isinstance(repository_id, bool) or not isinstance(repository_id, int) or repository_id <= 0:
        return None

    return repository_id


def extract_pull_request_number(payload: dict[str, object]) -> int | None:
    number = payload.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
        return None

    return number


def _extract_optional_string(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value:
        return value
    return None
