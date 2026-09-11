from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ReviewRisk, ReviewStatus, ReviewTriggerType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Review(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("pull_request_id", "commit_sha", "attempt_number"),
        CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        CheckConstraint("duration_ms IS NULL OR duration_ms >= 0", name="duration_ms_non_negative"),
        CheckConstraint("static_analysis_duration_ms IS NULL OR static_analysis_duration_ms >= 0", name="static_analysis_duration_ms_non_negative"),
        CheckConstraint("ai_analysis_duration_ms IS NULL OR ai_analysis_duration_ms >= 0", name="ai_analysis_duration_ms_non_negative"),
        CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="input_tokens_non_negative"),
        CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="output_tokens_non_negative"),
        CheckConstraint("total_tokens IS NULL OR total_tokens >= 0", name="total_tokens_non_negative"),
        CheckConstraint("estimated_cost_usd IS NULL OR estimated_cost_usd >= 0", name="estimated_cost_usd_non_negative"),
        Index("ix_reviews_pull_request_id", "pull_request_id"),
        Index("ix_reviews_status", "status"),
        Index("ix_reviews_overall_risk", "overall_risk"),
        Index("ix_reviews_commit_sha", "commit_sha"),
        Index("ix_reviews_started_at_id", "started_at", "id"),
    )

    pull_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pull_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(
            ReviewStatus,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="review_status",
            validate_strings=True,
            length=32,
        ),
        nullable=False,
    )
    overall_risk: Mapped[ReviewRisk | None] = mapped_column(
        Enum(
            ReviewRisk,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="review_risk",
            validate_strings=True,
            length=16,
        ),
        nullable=True,
    )
    trigger_type: Mapped[ReviewTriggerType] = mapped_column(
        Enum(
            ReviewTriggerType,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="review_trigger_type",
            validate_strings=True,
            length=24,
        ),
        nullable=False,
    )
    model_name: Mapped[str | None] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(100))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    static_analysis_duration_ms: Mapped[int | None] = mapped_column(Integer)
    ai_analysis_duration_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    pull_request: Mapped[PullRequest] = relationship(
        "PullRequest",
        back_populates="reviews",
    )
    findings: Mapped[list[ReviewFinding]] = relationship(
        "ReviewFinding",
        back_populates="review",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
