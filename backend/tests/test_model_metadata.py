from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy import Enum as SQLAlchemyEnum

from app.db.base import Base
from app.models.enums import (
    FindingCategory,
    FindingDiffSide,
    FindingSeverity,
    FindingSource,
    FindingStatus,
    PullRequestStatus,
    ReviewRisk,
    ReviewStatus,
    ReviewTriggerType,
    WebhookEventStatus,
)
import app.models  # noqa: F401


def constraint_columns(constraint: UniqueConstraint) -> tuple[str, ...]:
    return tuple(column.name for column in constraint.columns)


def check_constraint_names(table_name: str) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {
        constraint.name or ""
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def unique_constraints(table_name: str) -> set[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    return {
        constraint_columns(constraint)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def test_github_ingestion_tables_are_registered() -> None:
    assert {"repositories", "pull_requests", "webhook_events"}.issubset(Base.metadata.tables)


def test_review_tables_are_registered() -> None:
    assert {"reviews", "review_findings"}.issubset(Base.metadata.tables)


def test_required_columns_exist() -> None:
    expected_columns = {
        "repositories": {
            "id",
            "github_repository_id",
            "github_installation_id",
            "owner",
            "name",
            "full_name",
            "default_branch",
            "is_active",
            "created_at",
            "updated_at",
        },
        "pull_requests": {
            "id",
            "repository_id",
            "github_pr_number",
            "title",
            "author_login",
            "base_branch",
            "head_branch",
            "status",
            "head_sha",
            "html_url",
            "github_created_at",
            "github_updated_at",
            "created_at",
            "updated_at",
        },
        "webhook_events": {
            "id",
            "github_delivery_id",
            "event_name",
            "action",
            "github_repository_id",
            "github_pr_number",
            "payload",
            "payload_hash",
            "status",
            "attempt_count",
            "received_at",
            "processing_started_at",
            "processed_at",
            "error_message",
            "created_at",
            "updated_at",
        },
        "reviews": {
            "id",
            "pull_request_id",
            "commit_sha",
            "attempt_number",
            "status",
            "overall_risk",
            "trigger_type",
            "model_name",
            "model_version",
            "prompt_version",
            "duration_ms",
            "static_analysis_duration_ms",
            "ai_analysis_duration_ms",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "estimated_cost_usd",
            "error_code",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        },
        "review_findings": {
            "id",
            "review_id",
            "file_path",
            "start_line",
            "end_line",
            "diff_side",
            "severity",
            "category",
            "title",
            "problem",
            "explanation",
            "suggestion",
            "confidence",
            "source",
            "fingerprint",
            "code_snippet",
            "status",
            "github_comment_id",
            "published_to_github",
            "created_at",
            "updated_at",
        },
    }

    for table_name, columns in expected_columns.items():
        assert columns.issubset(Base.metadata.tables[table_name].columns.keys())


def test_repository_unique_constraints_exist() -> None:
    constraints = unique_constraints("repositories")

    assert ("github_repository_id",) in constraints
    assert ("full_name",) in constraints


def test_pull_request_repository_number_uniqueness_exists() -> None:
    assert ("repository_id", "github_pr_number") in unique_constraints("pull_requests")


def test_pull_request_positive_number_constraint_exists() -> None:
    assert "ck_pull_requests_github_pr_number_positive" in check_constraint_names("pull_requests")


def test_webhook_delivery_uniqueness_exists() -> None:
    assert ("github_delivery_id",) in unique_constraints("webhook_events")


def test_webhook_attempt_count_constraint_exists() -> None:
    assert "ck_webhook_events_attempt_count_non_negative" in check_constraint_names("webhook_events")


def test_pull_request_foreign_key_and_cascade_are_configured() -> None:
    table = Base.metadata.tables["pull_requests"]
    foreign_key_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_key_constraints) == 1
    assert foreign_key_constraints[0].referred_table.name == "repositories"
    assert foreign_key_constraints[0].ondelete == "CASCADE"


def test_enum_values_are_stored_as_snake_case_values() -> None:
    pull_request_status = Base.metadata.tables["pull_requests"].columns["status"].type
    webhook_event_status = Base.metadata.tables["webhook_events"].columns["status"].type

    assert isinstance(pull_request_status, SQLAlchemyEnum)
    assert pull_request_status.enums == [status.value for status in PullRequestStatus]
    assert pull_request_status.native_enum is False

    assert isinstance(webhook_event_status, SQLAlchemyEnum)
    assert webhook_event_status.enums == [status.value for status in WebhookEventStatus]
    assert webhook_event_status.native_enum is False


def test_review_enum_values_are_stored_as_snake_case_values() -> None:
    table_types = {
        "reviews.status": (Base.metadata.tables["reviews"].columns["status"].type, ReviewStatus),
        "reviews.overall_risk": (Base.metadata.tables["reviews"].columns["overall_risk"].type, ReviewRisk),
        "reviews.trigger_type": (Base.metadata.tables["reviews"].columns["trigger_type"].type, ReviewTriggerType),
        "review_findings.diff_side": (Base.metadata.tables["review_findings"].columns["diff_side"].type, FindingDiffSide),
        "review_findings.severity": (Base.metadata.tables["review_findings"].columns["severity"].type, FindingSeverity),
        "review_findings.category": (Base.metadata.tables["review_findings"].columns["category"].type, FindingCategory),
        "review_findings.source": (Base.metadata.tables["review_findings"].columns["source"].type, FindingSource),
        "review_findings.status": (Base.metadata.tables["review_findings"].columns["status"].type, FindingStatus),
    }

    for column_name, (column_type, enum_type) in table_types.items():
        assert isinstance(column_type, SQLAlchemyEnum), column_name
        assert column_type.enums == [status.value for status in enum_type]
        assert column_type.native_enum is False


def test_sync_columns_and_non_negative_checks() -> None:
    assert {"html_url", "description", "primary_language", "is_private", "github_updated_at", "last_synced_at"}.issubset(Base.metadata.tables["repositories"].columns.keys())
    assert {"is_draft", "additions", "deletions", "changed_files", "last_synced_at"}.issubset(Base.metadata.tables["pull_requests"].columns.keys())
    assert {f"ck_pull_requests_{field}_non_negative" for field in ("additions", "deletions", "changed_files")}.issubset(check_constraint_names("pull_requests"))


def test_review_identity_constraints_and_checks_exist() -> None:
    assert ("pull_request_id", "commit_sha", "attempt_number") in unique_constraints("reviews")
    assert {
        "ck_reviews_attempt_number_positive",
        "ck_reviews_duration_ms_non_negative",
        "ck_reviews_static_analysis_duration_ms_non_negative",
        "ck_reviews_ai_analysis_duration_ms_non_negative",
        "ck_reviews_input_tokens_non_negative",
        "ck_reviews_output_tokens_non_negative",
        "ck_reviews_total_tokens_non_negative",
        "ck_reviews_estimated_cost_usd_non_negative",
    }.issubset(check_constraint_names("reviews"))


def test_finding_identity_constraints_and_checks_exist() -> None:
    assert ("review_id", "fingerprint") in unique_constraints("review_findings")
    assert {
        "ck_review_findings_start_line_positive_when_present",
        "ck_review_findings_end_line_positive_when_present",
        "ck_review_findings_line_range_order",
        "ck_review_findings_confidence_between_zero_and_one",
        "ck_review_findings_fingerprint_length_64",
    }.issubset(check_constraint_names("review_findings"))


def test_review_foreign_keys_and_cascades_are_configured() -> None:
    review_fk = [
        constraint
        for constraint in Base.metadata.tables["reviews"].constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ][0]
    finding_fk = [
        constraint
        for constraint in Base.metadata.tables["review_findings"].constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ][0]

    assert review_fk.referred_table.name == "pull_requests"
    assert review_fk.ondelete == "CASCADE"
    assert finding_fk.referred_table.name == "reviews"
    assert finding_fk.ondelete == "CASCADE"


def test_review_indexes_exist() -> None:
    assert {index.name for index in Base.metadata.tables["reviews"].indexes} >= {
        "ix_reviews_pull_request_id",
        "ix_reviews_status",
        "ix_reviews_overall_risk",
        "ix_reviews_commit_sha",
        "ix_reviews_started_at_id",
    }
    assert {index.name for index in Base.metadata.tables["review_findings"].indexes} >= {
        "ix_review_findings_review_id",
        "ix_review_findings_severity",
        "ix_review_findings_category",
        "ix_review_findings_status",
        "ix_review_findings_source",
        "ix_review_findings_file_path",
    }
