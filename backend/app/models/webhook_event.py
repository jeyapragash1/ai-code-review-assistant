from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import WebhookEventStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class WebhookEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores raw GitHub payloads for later asynchronous processing and retry support."""

    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("github_delivery_id"),
        CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative"),
        CheckConstraint(
            "github_pr_number IS NULL OR github_pr_number > 0",
            name="github_pr_number_positive_when_present",
        ),
        CheckConstraint("length(payload_hash) = 64", name="payload_hash_length_64"),
        Index("ix_webhook_events_status", "status"),
        Index("ix_webhook_events_event_name", "event_name"),
        Index("ix_webhook_events_github_repository_id", "github_repository_id"),
        Index("ix_webhook_events_received_at", "received_at"),
    )

    github_delivery_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    github_repository_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    github_pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(
            WebhookEventStatus,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="webhook_event_status",
            validate_strings=True,
            length=20,
        ),
        nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
