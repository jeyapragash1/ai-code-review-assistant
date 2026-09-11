from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class GitHubOAuthTransaction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "github_oauth_transactions"
    __table_args__ = (
        UniqueConstraint("state_hash"),
        Index("ix_github_oauth_transactions_expires_at", "expires_at"),
    )

    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    code_verifier: Mapped[str] = mapped_column(String(128), nullable=False)
    next_path: Mapped[str | None] = mapped_column(String(2048))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
