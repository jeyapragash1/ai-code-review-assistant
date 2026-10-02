from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.repository import Repository


class GitHubCommit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "github_commits"
    __table_args__ = (
        UniqueConstraint("repository_id", "sha"),
        Index("ix_github_commits_repository_id", "repository_id"),
        Index("ix_github_commits_authored_at_id", "authored_at", "id"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    sha: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    author_name: Mapped[str | None] = mapped_column(String(255))
    author_login: Mapped[str | None] = mapped_column(String(255))
    committer_name: Mapped[str | None] = mapped_column(String(255))
    committer_login: Mapped[str | None] = mapped_column(String(255))
    authored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    html_url: Mapped[str | None] = mapped_column(String(2048))
    parent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    reference: Mapped[str | None] = mapped_column(String(255))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    repository: Mapped[Repository] = relationship("Repository")