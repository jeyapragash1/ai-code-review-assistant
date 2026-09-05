import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WebhookEvent, WebhookEventStatus

logger = logging.getLogger(__name__)

DELIVERY_UNIQUE_CONSTRAINT = "uq_webhook_events_github_delivery_id"


@dataclass(frozen=True)
class WebhookEventCreate:
    github_delivery_id: str
    event_name: str
    action: str | None
    github_repository_id: int | None
    github_pr_number: int | None
    payload: Mapping[str, object]
    payload_hash: str
    status: WebhookEventStatus
    received_at: datetime


class WebhookEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delivery_exists(self, delivery_id: str) -> bool:
        result = await self.session.scalar(
            select(WebhookEvent.id).where(WebhookEvent.github_delivery_id == delivery_id)
        )
        return result is not None

    async def create_if_not_exists(self, data: WebhookEventCreate) -> bool:
        if await self.delivery_exists(data.github_delivery_id):
            return False

        event = WebhookEvent(
            github_delivery_id=data.github_delivery_id,
            event_name=data.event_name,
            action=data.action,
            github_repository_id=data.github_repository_id,
            github_pr_number=data.github_pr_number,
            payload=dict(data.payload),
            payload_hash=data.payload_hash,
            status=data.status,
            attempt_count=0,
            received_at=data.received_at,
        )
        self.session.add(event)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if self._is_delivery_unique_violation(exc):
                logger.info(
                    "Duplicate webhook delivery detected during insert race.",
                    extra={
                        "delivery_id": data.github_delivery_id,
                        "event": data.event_name,
                        "action": data.action,
                    },
                )
                return False
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return True

    @staticmethod
    def _is_delivery_unique_violation(error: IntegrityError) -> bool:
        constraint_name = getattr(getattr(error, "orig", None), "diag", None)
        if constraint_name is not None:
            return getattr(constraint_name, "constraint_name", None) == DELIVERY_UNIQUE_CONSTRAINT

        return DELIVERY_UNIQUE_CONSTRAINT in str(error.orig)
