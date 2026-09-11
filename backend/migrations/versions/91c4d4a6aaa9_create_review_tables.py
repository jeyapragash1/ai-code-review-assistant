"""create review tables

Revision ID: 91c4d4a6aaa9
Revises: 2b28dd1f97e6
Create Date: 2026-09-11 03:57:51.193176+00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa



revision: str = '91c4d4a6aaa9'
down_revision: str | Sequence[str] | None = '2b28dd1f97e6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('reviews',
    sa.Column('pull_request_id', sa.UUID(), nullable=False),
    sa.Column('commit_sha', sa.String(length=40), nullable=False),
    sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False),
    sa.Column('status', sa.Enum('queued', 'fetching', 'static_analysis', 'ai_analysis', 'validating', 'publishing', 'completed', 'failed', name='review_status', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('overall_risk', sa.Enum('none', 'low', 'medium', 'high', name='review_risk', native_enum=False, create_constraint=True, length=16), nullable=True),
    sa.Column('trigger_type', sa.Enum('manual', 'webhook', 'synchronization', name='review_trigger_type', native_enum=False, create_constraint=True, length=24), nullable=False),
    sa.Column('model_name', sa.String(length=100), nullable=True),
    sa.Column('model_version', sa.String(length=100), nullable=True),
    sa.Column('prompt_version', sa.String(length=100), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('static_analysis_duration_ms', sa.Integer(), nullable=True),
    sa.Column('ai_analysis_duration_ms', sa.Integer(), nullable=True),
    sa.Column('input_tokens', sa.Integer(), nullable=True),
    sa.Column('output_tokens', sa.Integer(), nullable=True),
    sa.Column('total_tokens', sa.Integer(), nullable=True),
    sa.Column('estimated_cost_usd', sa.Numeric(precision=12, scale=6), nullable=True),
    sa.Column('error_code', sa.String(length=100), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('ai_analysis_duration_ms IS NULL OR ai_analysis_duration_ms >= 0', name=op.f('ck_reviews_ai_analysis_duration_ms_non_negative')),
    sa.CheckConstraint('attempt_number >= 1', name=op.f('ck_reviews_attempt_number_positive')),
    sa.CheckConstraint('duration_ms IS NULL OR duration_ms >= 0', name=op.f('ck_reviews_duration_ms_non_negative')),
    sa.CheckConstraint('estimated_cost_usd IS NULL OR estimated_cost_usd >= 0', name=op.f('ck_reviews_estimated_cost_usd_non_negative')),
    sa.CheckConstraint('input_tokens IS NULL OR input_tokens >= 0', name=op.f('ck_reviews_input_tokens_non_negative')),
    sa.CheckConstraint('output_tokens IS NULL OR output_tokens >= 0', name=op.f('ck_reviews_output_tokens_non_negative')),
    sa.CheckConstraint('static_analysis_duration_ms IS NULL OR static_analysis_duration_ms >= 0', name=op.f('ck_reviews_static_analysis_duration_ms_non_negative')),
    sa.CheckConstraint('total_tokens IS NULL OR total_tokens >= 0', name=op.f('ck_reviews_total_tokens_non_negative')),
    sa.ForeignKeyConstraint(['pull_request_id'], ['pull_requests.id'], name=op.f('fk_reviews_pull_request_id_pull_requests'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reviews')),
    sa.UniqueConstraint('pull_request_id', 'commit_sha', 'attempt_number', name=op.f('uq_reviews_pull_request_id_commit_sha_attempt_number'))
    )
    op.create_index('ix_reviews_commit_sha', 'reviews', ['commit_sha'], unique=False)
    op.create_index('ix_reviews_overall_risk', 'reviews', ['overall_risk'], unique=False)
    op.create_index('ix_reviews_pull_request_id', 'reviews', ['pull_request_id'], unique=False)
    op.create_index('ix_reviews_started_at_id', 'reviews', ['started_at', 'id'], unique=False)
    op.create_index('ix_reviews_status', 'reviews', ['status'], unique=False)
    op.create_table('review_findings',
    sa.Column('review_id', sa.UUID(), nullable=False),
    sa.Column('file_path', sa.String(length=1024), nullable=False),
    sa.Column('start_line', sa.Integer(), nullable=True),
    sa.Column('end_line', sa.Integer(), nullable=True),
    sa.Column('diff_side', sa.Enum('left', 'right', name='finding_diff_side', native_enum=False, create_constraint=True, length=10), nullable=True),
    sa.Column('severity', sa.Enum('high', 'medium', 'low', name='finding_severity', native_enum=False, create_constraint=True, length=16), nullable=False),
    sa.Column('category', sa.Enum('security', 'bug', 'validation', 'error_handling', 'performance', 'database', 'maintainability', 'code_quality', 'best_practice', name='finding_category', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('problem', sa.Text(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=True),
    sa.Column('suggestion', sa.Text(), nullable=True),
    sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column('source', sa.Enum('static', 'ai', 'hybrid', name='finding_source', native_enum=False, create_constraint=True, length=16), nullable=False),
    sa.Column('fingerprint', sa.String(length=64), nullable=False),
    sa.Column('code_snippet', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('open', 'dismissed', 'resolved', name='finding_status', native_enum=False, create_constraint=True, length=16), server_default='open', nullable=False),
    sa.Column('github_comment_id', sa.BigInteger(), nullable=True),
    sa.Column('published_to_github', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name=op.f('ck_review_findings_confidence_between_zero_and_one')),
    sa.CheckConstraint('end_line IS NULL OR end_line > 0', name=op.f('ck_review_findings_end_line_positive_when_present')),
    sa.CheckConstraint('length(fingerprint) = 64', name=op.f('ck_review_findings_fingerprint_length_64')),
    sa.CheckConstraint('start_line IS NULL OR end_line IS NULL OR end_line >= start_line', name=op.f('ck_review_findings_line_range_order')),
    sa.CheckConstraint('start_line IS NULL OR start_line > 0', name=op.f('ck_review_findings_start_line_positive_when_present')),
    sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], name=op.f('fk_review_findings_review_id_reviews'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_review_findings')),
    sa.UniqueConstraint('review_id', 'fingerprint', name=op.f('uq_review_findings_review_id_fingerprint'))
    )
    op.create_index('ix_review_findings_category', 'review_findings', ['category'], unique=False)
    op.create_index('ix_review_findings_file_path', 'review_findings', ['file_path'], unique=False)
    op.create_index('ix_review_findings_review_id', 'review_findings', ['review_id'], unique=False)
    op.create_index('ix_review_findings_severity', 'review_findings', ['severity'], unique=False)
    op.create_index('ix_review_findings_source', 'review_findings', ['source'], unique=False)
    op.create_index('ix_review_findings_status', 'review_findings', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_review_findings_status', table_name='review_findings')
    op.drop_index('ix_review_findings_source', table_name='review_findings')
    op.drop_index('ix_review_findings_severity', table_name='review_findings')
    op.drop_index('ix_review_findings_review_id', table_name='review_findings')
    op.drop_index('ix_review_findings_file_path', table_name='review_findings')
    op.drop_index('ix_review_findings_category', table_name='review_findings')
    op.drop_table('review_findings')
    op.drop_index('ix_reviews_status', table_name='reviews')
    op.drop_index('ix_reviews_started_at_id', table_name='reviews')
    op.drop_index('ix_reviews_pull_request_id', table_name='reviews')
    op.drop_index('ix_reviews_overall_risk', table_name='reviews')
    op.drop_index('ix_reviews_commit_sha', table_name='reviews')
    op.drop_table('reviews')
