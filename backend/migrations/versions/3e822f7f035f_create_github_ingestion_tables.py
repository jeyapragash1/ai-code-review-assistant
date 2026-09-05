"""create github ingestion tables

Revision ID: 3e822f7f035f
Revises: 
Create Date: 2026-09-05 08:54:13.412057+00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

revision: str = '3e822f7f035f'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('repositories',
    sa.Column('github_repository_id', sa.BigInteger(), nullable=False),
    sa.Column('github_installation_id', sa.BigInteger(), nullable=True),
    sa.Column('owner', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('full_name', sa.String(length=200), nullable=False),
    sa.Column('default_branch', sa.String(length=255), server_default='main', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_repositories')),
    sa.UniqueConstraint('full_name', name=op.f('uq_repositories_full_name')),
    sa.UniqueConstraint('github_repository_id', name=op.f('uq_repositories_github_repository_id'))
    )
    op.create_index('ix_repositories_github_installation_id', 'repositories', ['github_installation_id'], unique=False)
    op.create_index('ix_repositories_is_active', 'repositories', ['is_active'], unique=False)
    op.create_index('ix_repositories_owner_name', 'repositories', ['owner', 'name'], unique=False)
    op.create_table('webhook_events',
    sa.Column('github_delivery_id', sa.String(length=255), nullable=False),
    sa.Column('event_name', sa.String(length=100), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=True),
    sa.Column('github_repository_id', sa.BigInteger(), nullable=True),
    sa.Column('github_pr_number', sa.Integer(), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('payload_hash', sa.String(length=64), nullable=False),
    sa.Column('status', sa.Enum('received', 'processing', 'completed', 'failed', 'ignored', name='webhook_event_status', native_enum=False, create_constraint=True, length=20), nullable=False),
    sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('attempt_count >= 0', name=op.f('ck_webhook_events_attempt_count_non_negative')),
    sa.CheckConstraint('github_pr_number IS NULL OR github_pr_number > 0', name=op.f('ck_webhook_events_github_pr_number_positive_when_present')),
    sa.CheckConstraint('length(payload_hash) = 64', name=op.f('ck_webhook_events_payload_hash_length_64')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_webhook_events')),
    sa.UniqueConstraint('github_delivery_id', name=op.f('uq_webhook_events_github_delivery_id'))
    )
    op.create_index('ix_webhook_events_event_name', 'webhook_events', ['event_name'], unique=False)
    op.create_index('ix_webhook_events_github_repository_id', 'webhook_events', ['github_repository_id'], unique=False)
    op.create_index('ix_webhook_events_received_at', 'webhook_events', ['received_at'], unique=False)
    op.create_index('ix_webhook_events_status', 'webhook_events', ['status'], unique=False)
    op.create_table('pull_requests',
    sa.Column('repository_id', sa.UUID(), nullable=False),
    sa.Column('github_pr_number', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=512), nullable=False),
    sa.Column('author_login', sa.String(length=255), nullable=False),
    sa.Column('base_branch', sa.String(length=255), nullable=False),
    sa.Column('head_branch', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('open', 'closed', 'merged', name='pull_request_status', native_enum=False, create_constraint=True, length=20), nullable=False),
    sa.Column('head_sha', sa.String(length=40), nullable=False),
    sa.Column('html_url', sa.String(length=2048), nullable=True),
    sa.Column('github_created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('github_updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('github_pr_number > 0', name=op.f('ck_pull_requests_github_pr_number_positive')),
    sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], name=op.f('fk_pull_requests_repository_id_repositories'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pull_requests')),
    sa.UniqueConstraint('repository_id', 'github_pr_number', name=op.f('uq_pull_requests_repository_id_github_pr_number'))
    )
    op.create_index('ix_pull_requests_head_sha', 'pull_requests', ['head_sha'], unique=False)
    op.create_index('ix_pull_requests_repository_id', 'pull_requests', ['repository_id'], unique=False)
    op.create_index('ix_pull_requests_status', 'pull_requests', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_pull_requests_status', table_name='pull_requests')
    op.drop_index('ix_pull_requests_repository_id', table_name='pull_requests')
    op.drop_index('ix_pull_requests_head_sha', table_name='pull_requests')
    op.drop_table('pull_requests')
    op.drop_index('ix_webhook_events_status', table_name='webhook_events')
    op.drop_index('ix_webhook_events_received_at', table_name='webhook_events')
    op.drop_index('ix_webhook_events_github_repository_id', table_name='webhook_events')
    op.drop_index('ix_webhook_events_event_name', table_name='webhook_events')
    op.drop_table('webhook_events')
    op.drop_index('ix_repositories_owner_name', table_name='repositories')
    op.drop_index('ix_repositories_is_active', table_name='repositories')
    op.drop_index('ix_repositories_github_installation_id', table_name='repositories')
    op.drop_table('repositories')
