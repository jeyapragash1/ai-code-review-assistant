from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ActivityEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Public-safe event projection; never contains the original webhook payload."""
    __tablename__ = "activity_events"
    __table_args__ = (
        UniqueConstraint("github_delivery_id"), UniqueConstraint("idempotency_key"),
        Index("ix_activity_events_repository_id", "repository_id"),
        Index("ix_activity_events_event_type", "event_type"),
        Index("ix_activity_events_event_at_id", "event_at", "id"),
        Index("ix_activity_events_processing_status", "processing_status"),
    )
    github_delivery_id: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    installation_id: Mapped[UUID | None] = mapped_column(ForeignKey("github_installations.id", ondelete="SET NULL"))
    repository_id: Mapped[UUID | None] = mapped_column(ForeignKey("repositories.id", ondelete="SET NULL"))
    actor_github_id: Mapped[int | None] = mapped_column(BigInteger)
    actor_login: Mapped[str | None] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_action: Mapped[str | None] = mapped_column(String(100))
    safe_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(String(255))

