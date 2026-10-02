"""add GitHub issue persistence

Revision ID: e2f4a6b8c0d1
Revises: d1e7f3b2a5c9
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "e2f4a6b8c0d1"
down_revision: str | Sequence[str] | None = "d1e7f3b2a5c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_issues",
        sa.Column("repository_id", sa.UUID(), nullable=False),
        sa.Column("github_issue_id", sa.BigInteger(), nullable=False),
        sa.Column("github_issue_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("state_reason", sa.String(32)),
        sa.Column("author_login", sa.String(255)),
        sa.Column("author_github_id", sa.BigInteger()),
        sa.Column("assignees", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("labels", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("is_locked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("comment_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("html_url", sa.String(2048), nullable=False),
        sa.Column("github_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("github_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("github_closed_at", sa.DateTime(timezone=True)),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], name="fk_github_issues_repository_id_repositories", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_github_issues"),
        sa.UniqueConstraint("github_issue_id", name="uq_github_issues_github_issue_id"),
        sa.UniqueConstraint("repository_id", "github_issue_number", name="uq_github_issues_repository_id_github_issue_number"),
    )
    op.create_index("ix_github_issues_repository_id", "github_issues", ["repository_id"])
    op.create_index("ix_github_issues_state", "github_issues", ["state"])
    op.create_index("ix_github_issues_author_login", "github_issues", ["author_login"])
    op.create_index("ix_github_issues_updated_at_id", "github_issues", ["github_updated_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_github_issues_updated_at_id", table_name="github_issues")
    op.drop_index("ix_github_issues_author_login", table_name="github_issues")
    op.drop_index("ix_github_issues_state", table_name="github_issues")
    op.drop_index("ix_github_issues_repository_id", table_name="github_issues")
    op.drop_table("github_issues")
