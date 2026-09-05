from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Index, String, UniqueConstraint
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
    )

    github_repository_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    github_installation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    owner: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
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
