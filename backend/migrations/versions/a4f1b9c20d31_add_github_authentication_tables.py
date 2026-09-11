"""add GitHub authentication tables

Revision ID: a4f1b9c20d31
Revises: 91c4d4a6aaa9
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "a4f1b9c20d31"
down_revision: str | Sequence[str] | None = "91c4d4a6aaa9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("users", sa.Column("github_user_id", sa.BigInteger(), nullable=False), sa.Column("github_login", sa.String(255), nullable=False), sa.Column("github_login_normalized", sa.String(255), nullable=False), sa.Column("display_name", sa.String(255)), sa.Column("email", sa.String(320)), sa.Column("avatar_url", sa.String(2048)), sa.Column("profile_url", sa.String(2048)), sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False), sa.Column("last_login_at", sa.DateTime(timezone=True)), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.PrimaryKeyConstraint("id", name=op.f("pk_users")), sa.UniqueConstraint("github_user_id", name=op.f("uq_users_github_user_id")), sa.UniqueConstraint("github_login_normalized", name=op.f("uq_users_github_login_normalized")))
    op.create_index("ix_users_github_login_normalized", "users", ["github_login_normalized"])
    op.create_table("user_sessions", sa.Column("user_id", sa.UUID(), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("last_seen_at", sa.DateTime(timezone=True)), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_sessions_user_id_users"), ondelete="CASCADE"), sa.PrimaryKeyConstraint("id", name=op.f("pk_user_sessions")), sa.UniqueConstraint("token_hash", name=op.f("uq_user_sessions_token_hash")))
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])
    op.create_table("github_oauth_transactions", sa.Column("state_hash", sa.String(64), nullable=False), sa.Column("code_verifier", sa.String(128), nullable=False), sa.Column("next_path", sa.String(2048)), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("consumed_at", sa.DateTime(timezone=True)), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.PrimaryKeyConstraint("id", name=op.f("pk_github_oauth_transactions")), sa.UniqueConstraint("state_hash", name=op.f("uq_github_oauth_transactions_state_hash")))
    op.create_index("ix_github_oauth_transactions_expires_at", "github_oauth_transactions", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_github_oauth_transactions_expires_at", table_name="github_oauth_transactions")
    op.drop_table("github_oauth_transactions")
    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_users_github_login_normalized", table_name="users")
    op.drop_table("users")
