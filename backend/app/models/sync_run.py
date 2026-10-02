from datetime import datetime
from uuid import UUID
from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GitHubSyncRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "github_sync_runs"
    __table_args__ = (Index("ix_github_sync_runs_user_id_created_at", "user_id", "created_at"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(255))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
