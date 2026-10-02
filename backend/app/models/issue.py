from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.repository import Repository


class GitHubIssue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "github_issues"
    __table_args__ = (
        UniqueConstraint("github_issue_id"),
        UniqueConstraint("repository_id", "github_issue_number"),
        Index("ix_github_issues_repository_id", "repository_id"),
        Index("ix_github_issues_state", "state"),
        Index("ix_github_issues_author_login", "author_login"),
        Index("ix_github_issues_updated_at_id", "github_updated_at", "id"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    github_issue_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    github_issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    state_reason: Mapped[str | None] = mapped_column(String(32))
    author_login: Mapped[str | None] = mapped_column(String(255))
    author_github_id: Mapped[int | None] = mapped_column(BigInteger)
    assignees: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    labels: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    html_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    github_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    github_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    github_closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    repository: Mapped[Repository] = relationship("Repository")