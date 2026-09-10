from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Repository(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("github_repository_id"),
        UniqueConstraint("full_name"),
        Index("ix_repositories_github_installation_id", "github_installation_id"),
        Index("ix_repositories_owner_name", "owner", "name"),
        Index("ix_repositories_is_active", "is_active"),
        Index("ix_repositories_last_synced_at", "last_synced_at"),
    )

    github_repository_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    github_installation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    owner: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    html_url: Mapped[str | None] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(Text)
    primary_language: Mapped[str | None] = mapped_column(String(100))
    is_private: Mapped[bool | None] = mapped_column(Boolean)
    github_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    default_branch: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="main",
        server_default="main",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    pull_requests: Mapped[list[PullRequest]] = relationship(
        "PullRequest",
        back_populates="repository",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
