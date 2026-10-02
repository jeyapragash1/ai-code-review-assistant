import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.api.v1.access import accessible_repository_ids
from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.scoped_session import ScopedReadSession
from app.core.config import Settings
from app.db.session import get_db_session
from app.main import create_app
from app.models import ActivityEvent, PullRequest, Repository, ReviewJob, WebhookEvent, WebhookEventStatus, WebhookJob
from app.schemas.auth import AuthenticatedUser
from app.services.github.activity import event_timestamp, safe_metadata
from app.services.github.webhook_ingestion import GitHubWebhookIngestionService, SUPPORTED_EVENTS, determine_initial_status
from app.services.jobs import claim_job, finish_job, queue_review

NOW = datetime.now(UTC)
USER = AuthenticatedUser(id=uuid4(), github_user_id=41, github_login="owner", display_name=None, email=None,
    avatar_url=None, profile_url=None, session_expires_at=NOW + timedelta(hours=1))


def result(value):
    r = Mock()
    r.scalar_one_or_none.return_value = value
    r.scalar_one.return_value = value
    return r


@pytest.mark.parametrize("event", sorted(SUPPORTED_EVENTS))
def test_every_supported_event_is_ingested_without_network_or_analysis(event):
    repository = SimpleNamespace(create_if_not_exists=AsyncMock(return_value=True))
    service = GitHubWebhookIngestionService(repository)
    payload = {"action": "opened", "installation": {"id": 1}}
    r = asyncio.run(service.ingest(delivery_id=str(uuid4()), event_name=event, payload=payload, raw_body=b"{}"))
    assert r.status == (WebhookEventStatus.IGNORED if event == "ping" else WebhookEventStatus.RECEIVED)
    saved = repository.create_if_not_exists.call_args.args[0]
    assert saved.payload == payload
    assert saved.payload_hash


@pytest.mark.parametrize("event", sorted(SUPPORTED_EVENTS))
def test_duplicate_delivery_never_queues_again(event):
    repository = SimpleNamespace(create_if_not_exists=AsyncMock(return_value=False))
    r = asyncio.run(GitHubWebhookIngestionService(repository).ingest(delivery_id=str(uuid4()), event_name=event,
        payload={"action": "opened"}, raw_body=b"{}"))
    assert r.duplicate
    repository.create_if_not_exists.assert_awaited_once()


def test_activity_projection_excludes_payload_content_and_only_push_has_commit_metadata():
    payload = {"after": "a" * 40, "before": "b" * 40, "commits": [{"message": "private"}],
        "token": "private", "body": "private", "diff": "private", "created": True, "number": True}
    assert safe_metadata("push", payload) == {"after": "a" * 40, "before": "b" * 40, "created": True, "commit_count": 1}
    assert safe_metadata("issues", payload) == {}
    assert safe_metadata("push", {"after": "bad", "number": -1}) == {}
    assert event_timestamp({"issue": {"updated_at": "bad"}}, NOW) == NOW
    assert event_timestamp({"issue": {"updated_at": "2026-01-01T00:00:00Z"}}, NOW).year == 2026


@pytest.mark.parametrize("model", [ReviewJob, WebhookJob])
def test_queue_claim_locks_skips_locked_and_recovers_stale_leases(model):
    session = AsyncMock()
    job = SimpleNamespace(status="queued", retry_count=0)
    session.execute.side_effect = [result(None)] + ([result(None)] if model is ReviewJob else []) + [result(job)]
    claimed = asyncio.run(claim_job(session, model, Settings(_env_file=None)))
    statement = session.execute.call_args_list[-1].args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE SKIP LOCKED" in sql and "lease_until <=" in sql and "available_at <=" in sql
    assert claimed.status == "processing" and claimed.retry_count == 1 and claimed.lease_token
    assert claimed.lease_until > NOW
    session.commit.assert_awaited_once()


@pytest.mark.parametrize("attempt,status", [(1, "retryable"), (3, "failed")])
def test_failure_is_bounded_sanitized_and_fenced(attempt, status):
    session = AsyncMock()
    job = SimpleNamespace(id=uuid4(), retry_count=attempt, lease_token=uuid4())
    asyncio.run(finish_job(session, ReviewJob, job, Settings(_env_file=None), error=True))
    statement = session.execute.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    params = statement.compile().params
    assert "lease_token =" in sql and "status =" in sql
    assert params["status"] == status
    assert params["error_message"] == "Processing failed; check service configuration and permissions."
    assert params["lease_token"] is None


@pytest.mark.parametrize("completed", [False, True])
def test_review_queue_deduplicates_sha_and_reuses_completed_review(completed):
    session = AsyncMock()
    pr = SimpleNamespace(id=uuid4(), head_sha="a" * 40)
    review = SimpleNamespace(id=uuid4()) if completed else None
    job = SimpleNamespace(id=uuid4())
    session.execute.side_effect = [result(None), result(job)]
    with patch("app.services.jobs.ReviewStore") as store:
        store.return_value.completed_for_commit = AsyncMock(return_value=review)
        assert asyncio.run(queue_review(session, pr)) == job
    statement = session.execute.call_args_list[0].args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (pull_request_id, head_sha) DO NOTHING" in sql
    assert statement.compile().params["status"] == ("completed" if completed else "queued")


def test_scoped_reads_constrain_repository_and_review_aggregates():
    session = AsyncMock()
    scoped = ScopedReadSession(session, USER)
    asyncio.run(scoped.execute(select(Repository)))
    sql = str(session.execute.call_args.args[0].compile(dialect=postgresql.dialect()))
    assert "github_installations.account_github_id" in sql
    assert USER.github_user_id in session.execute.call_args.args[0].compile().params.values()
    access_sql = str(accessible_repository_ids(USER).compile(dialect=postgresql.dialect()))
    assert "is_active IS true" in access_sql and "suspended_at IS NULL" in access_sql


@pytest.mark.parametrize("path", ["/api/v1/activity", "/api/v1/dashboard/account-statistics", "/api/v1/github/sync/status",
    "/api/v1/pull-requests/00000000-0000-4000-8000-000000000001/review-jobs"])
def test_new_reads_require_authentication(path):
    with TestClient(create_app()) as client:
        assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", ["/api/v1/github/sync", "/api/v1/pull-requests/00000000-0000-4000-8000-000000000001/review-jobs"])
def test_mutations_require_same_origin(path):
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: USER
    async def db():
        yield AsyncMock()
    app.dependency_overrides[get_db_session] = db
    with TestClient(app) as client:
        assert client.post(path).status_code == 403
        assert client.post(path, headers={"Origin": "https://other.invalid"}).status_code == 403


def test_activity_filter_authorization_and_newest_first_sql():
    from app.api.v1.endpoints.activity import activity
    from app.schemas.pagination import PageParams
    session = AsyncMock()
    session.scalar.return_value = 0
    rows = Mock()
    rows.scalars.return_value.all.return_value = []
    session.execute.return_value = rows
    page = asyncio.run(activity(session, USER, PageParams(page=2, page_size=10), None, "push", "Owner", NOW - timedelta(days=1), NOW))
    assert page.total == 0
    sql = str(session.execute.call_args.args[0].compile(dialect=postgresql.dialect()))
    assert "account_github_id" in sql and "actor_login" in sql and "event_at DESC" in sql and "id DESC" in sql
    assert "LIMIT" in sql and "OFFSET" in sql


def test_new_schema_has_delivery_and_sha_uniqueness():
    from sqlalchemy import UniqueConstraint
    for model, keys in [(ActivityEvent, {("github_delivery_id",), ("idempotency_key",)}),
        (WebhookJob, {("webhook_event_id",)}), (ReviewJob, {("pull_request_id", "head_sha")})]:
        constraints = {tuple(c.columns.keys()) for c in model.__table__.constraints if isinstance(c, UniqueConstraint)}
        assert keys <= constraints
