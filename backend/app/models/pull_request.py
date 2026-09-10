from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PullRequestStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PullRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("repository_id", "github_pr_number"),
        CheckConstraint("github_pr_number > 0", name="github_pr_number_positive"),
        CheckConstraint("additions >= 0", name="additions_non_negative"),
        CheckConstraint("deletions >= 0", name="deletions_non_negative"),
        CheckConstraint("changed_files >= 0", name="changed_files_non_negative"),
        Index("ix_pull_requests_repository_id", "repository_id"),
        Index("ix_pull_requests_status", "status"),
        Index("ix_pull_requests_head_sha", "head_sha"),
        Index("ix_pull_requests_github_updated_at_id", "github_updated_at", "id"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    github_pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    author_login: Mapped[str] = mapped_column(String(255), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    head_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[PullRequestStatus] = mapped_column(
        Enum(
            PullRequestStatus,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="pull_request_status",
            validate_strings=True,
            length=20,
        ),
        nullable=False,
    )
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    html_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    github_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    github_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_draft: Mapped[bool | None] = mapped_column(Boolean)
    additions: Mapped[int | None] = mapped_column(Integer)
    deletions: Mapped[int | None] = mapped_column(Integer)
    changed_files: Mapped[int | None] = mapped_column(Integer)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    repository: Mapped[Repository] = relationship(
        "Repository",
        back_populates="pull_requests",
    )
