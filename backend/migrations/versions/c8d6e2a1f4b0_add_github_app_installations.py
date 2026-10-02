"""add GitHub App installations and repository access metadata

Revision ID: c8d6e2a1f4b0
Revises: a4f1b9c20d31
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c8d6e2a1f4b0"
down_revision: str | Sequence[str] | None = "a4f1b9c20d31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("repositories", sa.Column("github_pushed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("repositories", sa.Column("is_fork", sa.Boolean(), nullable=True))
    op.add_column("repositories", sa.Column("is_archived", sa.Boolean(), nullable=True))
    op.add_column("repositories", sa.Column("is_disabled", sa.Boolean(), nullable=True))
    op.add_column("repositories", sa.Column("stargazer_count", sa.BigInteger(), nullable=True))
    op.add_column("repositories", sa.Column("fork_count", sa.BigInteger(), nullable=True))
    op.add_column("repositories", sa.Column("open_issue_count", sa.BigInteger(), nullable=True))
    op.create_table(
        "github_installations",
        sa.Column("github_installation_id", sa.BigInteger(), nullable=False),
        sa.Column("account_github_id", sa.BigInteger(), nullable=False),
        sa.Column("account_login", sa.String(length=255), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("repository_selection", sa.String(length=32), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=True),
        sa.Column("events", sa.JSON(), nullable=True),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("github_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("github_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_github_installations"),
        sa.UniqueConstraint("github_installation_id", name="uq_github_installations_github_installation_id"),
    )
    op.create_index("ix_github_installations_account_login", "github_installations", ["account_login"])
    op.create_index("ix_github_installations_is_active", "github_installations", ["is_active"])
    op.create_table(
        "installation_repository_access",
        sa.Column("installation_id", sa.UUID(), nullable=False),
        sa.Column("repository_id", sa.UUID(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["installation_id"], ["github_installations.id"], name="fk_ira_installation_id_github_installations", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], name="fk_ira_repository_id_repositories", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_installation_repository_access"),
        sa.UniqueConstraint("installation_id", "repository_id", name="uq_installation_repository_access_installation_id"),
    )
    op.create_index("ix_installation_repository_access_repository_id", "installation_repository_access", ["repository_id"])
    op.create_index("ix_installation_repository_access_is_active", "installation_repository_access", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_installation_repository_access_is_active", table_name="installation_repository_access")
    op.drop_index("ix_installation_repository_access_repository_id", table_name="installation_repository_access")
    op.drop_table("installation_repository_access")
    op.drop_index("ix_github_installations_is_active", table_name="github_installations")
    op.drop_index("ix_github_installations_account_login", table_name="github_installations")
    op.drop_table("github_installations")
    for column in ("open_issue_count", "fork_count", "stargazer_count", "is_disabled", "is_archived", "is_fork", "github_pushed_at"):
        op.drop_column("repositories", column)
