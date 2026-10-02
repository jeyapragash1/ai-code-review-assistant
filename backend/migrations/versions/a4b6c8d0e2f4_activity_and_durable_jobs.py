"""Permanent activity projections and durable webhook/review queues."""
from alembic import op
import sqlalchemy as sa

revision = "a4b6c8d0e2f4"
down_revision = "f3a5c7e9b1d2"
branch_labels = None
depends_on = None


def timestamps():
    return [sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())]


def upgrade():
    op.create_table("github_sync_runs", *timestamps(),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False), sa.Column("error_message", sa.String(255)),
        sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.create_index("ix_github_sync_runs_user_id_created_at", "github_sync_runs", ["user_id", "created_at"])
    op.create_table("activity_events", *timestamps(),
        sa.Column("github_delivery_id", sa.String(255)),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("installation_id", sa.UUID(), sa.ForeignKey("github_installations.id", ondelete="SET NULL")),
        sa.Column("repository_id", sa.UUID(), sa.ForeignKey("repositories.id", ondelete="SET NULL")),
        sa.Column("actor_github_id", sa.BigInteger()), sa.Column("actor_login", sa.String(255)),
        sa.Column("event_type", sa.String(100), nullable=False), sa.Column("event_action", sa.String(100)),
        sa.Column("safe_metadata", sa.JSON(), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processing_status", sa.String(20), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(255)),
        sa.UniqueConstraint("github_delivery_id"), sa.UniqueConstraint("idempotency_key"))
    for columns in [("repository_id",), ("event_type",), ("event_at", "id"), ("processing_status",)]:
        op.create_index("ix_activity_events_" + "_".join(columns), "activity_events", list(columns))
    for table in ("webhook_jobs", "review_jobs"):
        specific = ([sa.Column("webhook_event_id", sa.UUID(), sa.ForeignKey("webhook_events.id", ondelete="RESTRICT"), nullable=False), sa.UniqueConstraint("webhook_event_id")]
                    if table == "webhook_jobs" else [
                        sa.Column("pull_request_id", sa.UUID(), sa.ForeignKey("pull_requests.id", ondelete="RESTRICT"), nullable=False),
                        sa.Column("head_sha", sa.String(40), nullable=False),
                        sa.Column("review_id", sa.UUID(), sa.ForeignKey("reviews.id", ondelete="SET NULL")),
                        sa.UniqueConstraint("pull_request_id", "head_sha")])
        op.create_table(table, *timestamps(), *specific,
            sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("lease_until", sa.DateTime(timezone=True)), sa.Column("lease_token", sa.UUID()),
            sa.Column("error_message", sa.String(255)), sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.CheckConstraint("retry_count >= 0 AND retry_count <= 5", name="retry_bounds"),
            sa.CheckConstraint("status IN ('queued','processing','completed','failed','retryable')", name="valid_status"))
        op.create_index("ix_" + table + "_status_available_at", table, ["status", "available_at"])
        op.create_index("ix_" + table + "_lease_until", table, ["lease_until"])
    # Existing signed deliveries are queued once; ignored deliveries remain ignored.
    op.execute("INSERT INTO webhook_jobs (id, webhook_event_id) SELECT id, id FROM webhook_events WHERE status IN ('received','failed','processing') ON CONFLICT DO NOTHING")


def downgrade():
    op.drop_table("review_jobs")
    op.drop_table("webhook_jobs")
    op.drop_table("activity_events")
    op.drop_table("github_sync_runs")
