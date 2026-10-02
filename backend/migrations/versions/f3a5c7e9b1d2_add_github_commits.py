"""add metadata-only GitHub commits

Revision ID: f3a5c7e9b1d2
Revises: e2f4a6b8c0d1
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "f3a5c7e9b1d2"
down_revision: str | Sequence[str] | None = "e2f4a6b8c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_commits",
        sa.Column("repository_id", sa.UUID(), nullable=False), sa.Column("sha", sa.String(40), nullable=False),
        sa.Column("title", sa.String(512), nullable=False), sa.Column("message", sa.Text()),
        sa.Column("author_name", sa.String(255)), sa.Column("author_login", sa.String(255)),
        sa.Column("committer_name", sa.String(255)), sa.Column("committer_login", sa.String(255)),
        sa.Column("authored_at", sa.DateTime(timezone=True)), sa.Column("committed_at", sa.DateTime(timezone=True)),
        sa.Column("html_url", sa.String(2048)), sa.Column("parent_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reference", sa.String(255)), sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], name="fk_github_commits_repository_id_repositories", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_github_commits"), sa.UniqueConstraint("repository_id", "sha", name="uq_github_commits_repository_id_sha"),
    )
    op.create_index("ix_github_commits_repository_id", "github_commits", ["repository_id"])
    op.create_index("ix_github_commits_authored_at_id", "github_commits", ["authored_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_github_commits_authored_at_id", table_name="github_commits")
    op.drop_index("ix_github_commits_repository_id", table_name="github_commits")
    op.drop_table("github_commits")
