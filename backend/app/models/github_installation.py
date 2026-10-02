from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.repository import Repository


class GitHubInstallation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "github_installations"
    __table_args__ = (
        UniqueConstraint("github_installation_id"),
        Index("ix_github_installations_account_login", "account_login"),
        Index("ix_github_installations_is_active", "is_active"),
    )

    github_installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_github_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_login: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    repository_selection: Mapped[str] = mapped_column(String(32), nullable=False)
    permissions: Mapped[dict | None] = mapped_column(JSON)
    events: Mapped[list | None] = mapped_column(JSON)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    github_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    github_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    repository_access: Mapped[list[InstallationRepositoryAccess]] = relationship(
        "InstallationRepositoryAccess", back_populates="installation", cascade="all, delete-orphan", passive_deletes=True
    )


class InstallationRepositoryAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "installation_repository_access"
    __table_args__ = (
        UniqueConstraint("installation_id", "repository_id"),
        Index("ix_installation_repository_access_repository_id", "repository_id"),
        Index("ix_installation_repository_access_is_active", "is_active"),
    )

    installation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("github_installations.id", ondelete="CASCADE"), nullable=False)
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    installation: Mapped[GitHubInstallation] = relationship("GitHubInstallation", back_populates="repository_access")
    repository: Mapped[Repository] = relationship("Repository")