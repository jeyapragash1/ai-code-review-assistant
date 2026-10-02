"""Durable queues. Authenticated delivery payloads stay in webhook_events only."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class JobFields:
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued", server_default="queued")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[UUID | None]
    error_message: Mapped[str | None] = mapped_column(String(255))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WebhookJob(UUIDPrimaryKeyMixin, TimestampMixin, JobFields, Base):
    __tablename__ = "webhook_jobs"
    __table_args__ = (
        UniqueConstraint("webhook_event_id"),
        CheckConstraint("retry_count >= 0 AND retry_count <= 5", name="retry_bounds"),
        CheckConstraint("status IN ('queued','processing','completed','failed','retryable')", name="valid_status"),
        Index("ix_webhook_jobs_status_available_at", "status", "available_at"),
        Index("ix_webhook_jobs_lease_until", "lease_until"),
    )
    webhook_event_id: Mapped[UUID] = mapped_column(ForeignKey("webhook_events.id", ondelete="RESTRICT"), nullable=False)


class ReviewJob(UUIDPrimaryKeyMixin, TimestampMixin, JobFields, Base):
    __tablename__ = "review_jobs"
    __table_args__ = (
        UniqueConstraint("pull_request_id", "head_sha"),
        CheckConstraint("retry_count >= 0 AND retry_count <= 5", name="retry_bounds"),
        CheckConstraint("status IN ('queued','processing','completed','failed','retryable')", name="valid_status"),
        Index("ix_review_jobs_status_available_at", "status", "available_at"),
        Index("ix_review_jobs_lease_until", "lease_until"),
    )
    pull_request_id: Mapped[UUID] = mapped_column(ForeignKey("pull_requests.id", ondelete="RESTRICT"), nullable=False)
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(20), nullable=False, default="manual", server_default="manual")
    review_id: Mapped[UUID | None] = mapped_column(ForeignKey("reviews.id", ondelete="SET NULL"))
