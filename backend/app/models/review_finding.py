from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Enum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import FindingCategory, FindingDiffSide, FindingSeverity, FindingSource, FindingStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ReviewFinding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_findings"
    __table_args__ = (
        UniqueConstraint("review_id", "fingerprint"),
        CheckConstraint("start_line IS NULL OR start_line > 0", name="start_line_positive_when_present"),
        CheckConstraint("end_line IS NULL OR end_line > 0", name="end_line_positive_when_present"),
        CheckConstraint("start_line IS NULL OR end_line IS NULL OR end_line >= start_line", name="line_range_order"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_between_zero_and_one"),
        CheckConstraint("length(fingerprint) = 64", name="fingerprint_length_64"),
        Index("ix_review_findings_review_id", "review_id"),
        Index("ix_review_findings_severity", "severity"),
        Index("ix_review_findings_category", "category"),
        Index("ix_review_findings_status", "status"),
        Index("ix_review_findings_source", "source"),
        Index("ix_review_findings_file_path", "file_path"),
    )

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    diff_side: Mapped[FindingDiffSide | None] = mapped_column(
        Enum(
            FindingDiffSide,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="finding_diff_side",
            validate_strings=True,
            length=10,
        ),
        nullable=True,
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(
            FindingSeverity,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="finding_severity",
            validate_strings=True,
            length=16,
        ),
        nullable=False,
    )
    category: Mapped[FindingCategory] = mapped_column(
        Enum(
            FindingCategory,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="finding_category",
            validate_strings=True,
            length=32,
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    source: Mapped[FindingSource] = mapped_column(
        Enum(
            FindingSource,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="finding_source",
            validate_strings=True,
            length=16,
        ),
        nullable=False,
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    code_snippet: Mapped[str | None] = mapped_column(Text)
    status: Mapped[FindingStatus] = mapped_column(
        Enum(
            FindingStatus,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            native_enum=False,
            create_constraint=True,
            name="finding_status",
            validate_strings=True,
            length=16,
        ),
        nullable=False,
        default=FindingStatus.OPEN,
        server_default=FindingStatus.OPEN.value,
    )
    github_comment_id: Mapped[int | None] = mapped_column(BigInteger)
    published_to_github: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    review: Mapped[Review] = relationship(
        "Review",
        back_populates="findings",
    )
