from uuid import UUID
from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserInstallationAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Explicit administrator grant for organization installation visibility."""
    __tablename__ = "user_installation_access"
    __table_args__ = (UniqueConstraint("user_id", "installation_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    installation_id: Mapped[UUID] = mapped_column(ForeignKey("github_installations.id", ondelete="CASCADE"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class UserRepositoryAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Ownership grants for repositories synchronized before App installation setup."""
    __tablename__ = "user_repository_access"
    __table_args__ = (UniqueConstraint("user_id", "repository_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repository_id: Mapped[UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
