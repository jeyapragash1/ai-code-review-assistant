import json
import logging
import re
from typing import Annotated
from typing import Any

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session
from app.models import WebhookEventStatus
from app.repositories.webhook_event import WebhookEventRepository
from app.schemas.webhook import (
    WebhookAcceptedResponse,
    WebhookDuplicateResponse,
    WebhookIgnoredResponse,
    WebhookPingResponse,
)
from app.services.github.webhook_ingestion import (
    GitHubWebhookIngestionService,
    WebhookPersistenceError,
)
from app.services.github.webhook_security import verify_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

DELIVERY_ID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
MAX_HEADER_LENGTH = 255


def get_webhook_ingestion_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GitHubWebhookIngestionService:
    return GitHubWebhookIngestionService(WebhookEventRepository(session))


@router.post(
    "/github",
    response_model=None,
    responses={
        200: {"model": WebhookPingResponse | WebhookDuplicateResponse},
        202: {"model": WebhookAcceptedResponse | WebhookIgnoredResponse},
    },
)
async def github_webhook(
    request: Request,
    ingestion_service: Annotated[
        GitHubWebhookIngestionService,
        Depends(get_webhook_ingestion_service),
    ],
    x_hub_signature_256: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
    x_github_event: Annotated[str | None, Header(alias="X-GitHub-Event")] = None,
    x_github_delivery: Annotated[str | None, Header(alias="X-GitHub-Delivery")] = None,
) -> Any:
    secret = settings.github_webhook_secret
    if not secret.strip():
        logger.error("Webhook endpoint unavailable due to server configuration.")
        return _error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "Service unavailable.")

    header_error = _validate_headers(x_hub_signature_256, x_github_event, x_github_delivery)
    if header_error is not None:
        return header_error

    content_type = request.headers.get("content-type", "")
    if not _is_json_content_type(content_type):
        return _error_response(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported content type.")

    max_body_bytes = settings.github_webhook_max_body_bytes
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError:
            return _error_response(status.HTTP_400_BAD_REQUEST, "Invalid content length.")
        if declared_length > max_body_bytes:
            return _error_response(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Payload too large.")

    raw_body = await request.body()
    if len(raw_body) > max_body_bytes:
        return _error_response(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Payload too large.")

    if not verify_signature(secret, raw_body, x_hub_signature_256 or ""):
        return _error_response(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature.")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return _error_response(status.HTTP_400_BAD_REQUEST, "Invalid JSON payload.")

    if not isinstance(payload, dict):
        return _error_response(status.HTTP_400_BAD_REQUEST, "Invalid JSON payload.")

    try:
        result = await ingestion_service.ingest(
            delivery_id=x_github_delivery or "",
            event_name=x_github_event or "",
            payload=payload,
            raw_body=raw_body,
        )
    except WebhookPersistenceError:
        logger.error(
            "Webhook persistence failed.",
            extra={"delivery_id": x_github_delivery, "event": x_github_event},
        )
        return _error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "Service unavailable.")

    if result.duplicate:
        return WebhookDuplicateResponse(
            status="duplicate",
            delivery_id=result.delivery_id,
            event=result.event,
        )

    if result.event == "ping":
        return WebhookPingResponse(
            status="pong",
            delivery_id=result.delivery_id,
            event="ping",
        )

    if result.status == WebhookEventStatus.RECEIVED:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=WebhookAcceptedResponse(
                status="accepted",
                delivery_id=result.delivery_id,
                event="pull_request",
                action=result.action or "",
            ).model_dump(),
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=WebhookIgnoredResponse(
            status="ignored",
            delivery_id=result.delivery_id,
            event=result.event,
            action=result.action,
        ).model_dump(exclude_none=True),
    )


def _validate_headers(
    signature: str | None,
    event: str | None,
    delivery: str | None,
) -> JSONResponse | None:
    if signature is None:
        return _error_response(status.HTTP_401_UNAUTHORIZED, "Missing webhook signature.")
    if event is None:
        return _error_response(status.HTTP_400_BAD_REQUEST, "Missing GitHub event header.")
    if delivery is None:
        return _error_response(status.HTTP_400_BAD_REQUEST, "Missing GitHub delivery header.")

    if len(signature) > MAX_HEADER_LENGTH or len(event) > MAX_HEADER_LENGTH or len(delivery) > MAX_HEADER_LENGTH:
        return _error_response(status.HTTP_400_BAD_REQUEST, "Invalid GitHub webhook headers.")
    if not event or not event.replace("_", "").replace("-", "").isalnum():
        return _error_response(status.HTTP_400_BAD_REQUEST, "Invalid GitHub event header.")
    if DELIVERY_ID_PATTERN.fullmatch(delivery) is None:
        return _error_response(status.HTTP_400_BAD_REQUEST, "Invalid GitHub delivery header.")

    return None


def _is_json_content_type(content_type: str) -> bool:
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type == "application/json"


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": message})
