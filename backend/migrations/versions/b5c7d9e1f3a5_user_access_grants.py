"""Explicit user access grants; preserve pre-installation personal repositories."""
from alembic import op
import sqlalchemy as sa

revision = "b5c7d9e1f3a5"
down_revision = "a4b6c8d0e2f4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("review_jobs", sa.Column("trigger_type", sa.String(20), nullable=False, server_default="manual"))
    for table, target, column in [("user_installation_access", "github_installations", "installation_id"),
        ("user_repository_access", "repositories", "repository_id")]:
        op.create_table(table,
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column(column, sa.UUID(), sa.ForeignKey(target + ".id", ondelete="CASCADE"), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", column))
    # Only personal owner matches get a legacy grant. Organization access is
    # never inferred from an allowlisted login. No existing IDs are changed.
    op.execute("""INSERT INTO user_repository_access (id, user_id, repository_id)
        SELECT gen_random_uuid(), u.id, r.id FROM users u JOIN repositories r
        ON lower(r.owner) = u.github_login_normalized
        WHERE NOT EXISTS (SELECT 1 FROM installation_repository_access a WHERE a.repository_id = r.id)
        ON CONFLICT DO NOTHING""")


def downgrade():
    op.drop_column("review_jobs", "trigger_type")
    op.drop_table("user_repository_access")
    op.drop_table("user_installation_access")
