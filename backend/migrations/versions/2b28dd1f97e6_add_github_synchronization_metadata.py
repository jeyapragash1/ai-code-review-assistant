"""add github synchronization metadata

Revision ID: 2b28dd1f97e6
Revises: 3e822f7f035f
Create Date: 2026-09-10 04:28:26.619578+00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa



revision: str = '2b28dd1f97e6'
down_revision: str | Sequence[str] | None = '3e822f7f035f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable metadata preserves unknown values on legacy unsynchronized records.
    op.add_column('pull_requests', sa.Column('is_draft', sa.Boolean(), nullable=True))
    op.add_column('pull_requests', sa.Column('additions', sa.Integer(), nullable=True))
    op.add_column('pull_requests', sa.Column('deletions', sa.Integer(), nullable=True))
    op.add_column('pull_requests', sa.Column('changed_files', sa.Integer(), nullable=True))
    op.add_column('pull_requests', sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(op.f('ck_pull_requests_additions_non_negative'), 'pull_requests', 'additions >= 0')
    op.create_check_constraint(op.f('ck_pull_requests_deletions_non_negative'), 'pull_requests', 'deletions >= 0')
    op.create_check_constraint(op.f('ck_pull_requests_changed_files_non_negative'), 'pull_requests', 'changed_files >= 0')
    op.create_index('ix_pull_requests_github_updated_at_id', 'pull_requests', ['github_updated_at', 'id'], unique=False)
    op.add_column('repositories', sa.Column('html_url', sa.String(length=2048), nullable=True))
    op.add_column('repositories', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('repositories', sa.Column('primary_language', sa.String(length=100), nullable=True))
    op.add_column('repositories', sa.Column('is_private', sa.Boolean(), nullable=True))
    op.add_column('repositories', sa.Column('github_updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('repositories', sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_repositories_last_synced_at', 'repositories', ['last_synced_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_repositories_last_synced_at', table_name='repositories')
    op.drop_column('repositories', 'last_synced_at')
    op.drop_column('repositories', 'github_updated_at')
    op.drop_column('repositories', 'is_private')
    op.drop_column('repositories', 'primary_language')
    op.drop_column('repositories', 'description')
    op.drop_column('repositories', 'html_url')
    op.drop_index('ix_pull_requests_github_updated_at_id', table_name='pull_requests')
    op.drop_constraint(op.f('ck_pull_requests_changed_files_non_negative'), 'pull_requests', type_='check')
    op.drop_constraint(op.f('ck_pull_requests_deletions_non_negative'), 'pull_requests', type_='check')
    op.drop_constraint(op.f('ck_pull_requests_additions_non_negative'), 'pull_requests', type_='check')
    op.drop_column('pull_requests', 'last_synced_at')
    op.drop_column('pull_requests', 'changed_files')
    op.drop_column('pull_requests', 'deletions')
    op.drop_column('pull_requests', 'additions')
    op.drop_column('pull_requests', 'is_draft')
