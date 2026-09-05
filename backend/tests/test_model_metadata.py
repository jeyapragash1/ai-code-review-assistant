from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy import Enum as SQLAlchemyEnum

from app.db.base import Base
from app.models.enums import PullRequestStatus, WebhookEventStatus
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
