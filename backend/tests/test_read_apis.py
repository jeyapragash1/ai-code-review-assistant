import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.read_dependencies import pull_request_store, repository_store, review_finding_store, review_store
from app.api.v1.auth_dependencies import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.db.session import get_db_session
from app.main import create_app
from app.models import (
    FindingCategory,
    FindingSeverity,
    FindingSource,
    FindingStatus,
    PullRequest,
    PullRequestStatus,
    Repository,
    Review,
    ReviewRisk,
    ReviewStatus,
    ReviewTriggerType,
)
from app.repositories.pull_request import PullRequestStore
from app.repositories.repository import RepositoryStore
from app.repositories.review import ReviewFindingStore, ReviewStore
from app.schemas.pagination import PageParams, paginated
from app.schemas.repository import RepositoryResponse
from app.schemas.review import ReviewFindingResponse, ReviewResponse


@pytest.fixture
def api():
    app = create_app()
    repo_store = AsyncMock()
    pr_store = AsyncMock()
    reviews = AsyncMock()
    findings = AsyncMock()
    repo_store.list.return_value = paginated([], 0, PageParams())
    pr_store.list.return_value = paginated([], 0, PageParams())
    reviews.list.return_value = paginated([], 0, PageParams())
    findings.list.return_value = paginated([], 0, PageParams())
    repo_store.get.return_value = None
    pr_store.get.return_value = None
    reviews.get.return_value = None
    findings.get.return_value = None
    app.dependency_overrides[repository_store] = lambda: repo_store
    app.dependency_overrides[pull_request_store] = lambda: pr_store
    app.dependency_overrides[review_store] = lambda: reviews
    app.dependency_overrides[review_finding_store] = lambda: findings
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=uuid4(), github_user_id=1, github_login="test", display_name=None,
        email=None, avatar_url=None, profile_url=None, session_expires_at=datetime.now(UTC),
    )
    with TestClient(app) as client:
        yield client, repo_store, pr_store, reviews, findings


@pytest.mark.parametrize("path", [
    "/repositories?page=0", "/repositories?page_size=101", "/repositories?page_size=0",
    "/repositories?page=foo", "/repositories?is_active=maybe", "/repositories?search=",
    "/pull-requests?status=unknown", "/pull-requests?repository_id=invalid", "/pull-requests?page=-1",
    "/repositories/not-a-uuid", "/pull-requests/not-a-uuid", "/repositories?search=" + "x" * 201,
    "/reviews?status=unknown", "/reviews?overall_risk=severe", "/reviews?commit_sha=short",
    "/reviews?pull_request_id=invalid", "/reviews?repository_id=invalid", "/reviews/not-a-uuid",
    "/review-findings/not-a-uuid", "/reviews/" + str(uuid4()) + "/findings?severity=critical",
    "/reviews/" + str(uuid4()) + "/findings?category=unknown", "/reviews/" + str(uuid4()) + "/findings?source=tool",
    "/reviews/" + str(uuid4()) + "/findings?file_path=",
])
def test_query_and_uuid_validation(api, path):
    client, *_ = api
    assert client.get("/api/v1" + path).status_code == 422


def test_repository_filters_are_forwarded(api):
    client, repos, *_ = api
    response = client.get("/api/v1/repositories?page=2&page_size=5&search=example&is_active=false")
    assert response.status_code == 200
    args = repos.list.call_args.args
    assert args[0] == PageParams(page=2, page_size=5)
    assert args[1:] == ("example", False)
    assert set(response.json()) == {"items", "total", "page", "page_size", "total_pages"}


def test_pr_filters_are_forwarded(api):
    client, _, prs, *_ = api
    repo_id = uuid4()
    response = client.get(f"/api/v1/pull-requests?repository_id={repo_id}&search=fix&status=merged")
    assert response.status_code == 200
    assert prs.list.call_args.args[1:] == ("fix", repo_id, PullRequestStatus.MERGED)


@pytest.mark.parametrize("path", ["/repositories/", "/pull-requests/"])
def test_missing_record_404(api, path):
    assert api[0].get("/api/v1" + path + str(uuid4())).status_code == 404


def test_nested_pr_endpoint_checks_repository(api):
    client, repos, prs, *_ = api
    repo_id = uuid4()
    assert client.get(f"/api/v1/repositories/{repo_id}/pull-requests").status_code == 404
    prs.list.assert_not_awaited()
    repos.get.return_value = Mock()
    response = client.get(f"/api/v1/repositories/{repo_id}/pull-requests?status=open&page_size=10")
    assert response.status_code == 200
    assert prs.list.call_args.kwargs == {"repository_id": repo_id, "status": PullRequestStatus.OPEN}


def test_repository_response_is_explicit(api):
    client, repos, *_ = api
    now = datetime.now(UTC)
    repo_id = uuid4()
    repos.get.return_value = RepositoryResponse(
        id=repo_id, full_name="octocat/example", html_url="https://github.com/octocat/example",
        github_repository_id=101, owner="octocat", name="example", description=None,
        default_branch="main", primary_language="Python", is_private=False, is_active=True,
        github_updated_at=now, last_synced_at=now, created_at=now, updated_at=now,
        pull_request_count=4, open_pull_request_count=2,
    )
    response = client.get(f"/api/v1/repositories/{repo_id}")
    assert response.status_code == 200
    assert response.json()["pull_request_count"] == 4
    assert "payload" not in response.json() and "github_token" not in response.json()


def test_review_filters_are_forwarded(api):
    client, _, _, reviews, _ = api
    pr_id = uuid4()
    repo_id = uuid4()
    response = client.get(
        f"/api/v1/reviews?pull_request_id={pr_id}&repository_id={repo_id}&status=completed&overall_risk=high&commit_sha=abcdef1"
    )
    assert response.status_code == 200
    assert reviews.list.call_args.args[1:] == (pr_id, repo_id, ReviewStatus.COMPLETED, ReviewRisk.HIGH, "abcdef1")


def test_review_and_finding_404s(api):
    client, *_ = api
    assert client.get(f"/api/v1/reviews/{uuid4()}").status_code == 404
    assert client.get(f"/api/v1/review-findings/{uuid4()}").status_code == 404


def test_nested_pull_request_reviews_checks_parent(api):
    client, _, prs, reviews, _ = api
    pr_id = uuid4()
    assert client.get(f"/api/v1/pull-requests/{pr_id}/reviews").status_code == 404
    reviews.list.assert_not_awaited()
    prs.get.return_value = Mock()
    response = client.get(f"/api/v1/pull-requests/{pr_id}/reviews?page_size=10")
    assert response.status_code == 200
    assert reviews.list.call_args.kwargs == {"pull_request_id": pr_id}


def test_nested_review_findings_checks_parent_and_forwards_filters(api):
    client, _, _, reviews, findings = api
    review_id = uuid4()
    assert client.get(f"/api/v1/reviews/{review_id}/findings").status_code == 404
    findings.list.assert_not_awaited()
    reviews.get.return_value = Mock()
    response = client.get(
        f"/api/v1/reviews/{review_id}/findings?severity=high&category=security&status=open&source=ai&file_path=app.py&page_size=10"
    )
    assert response.status_code == 200
    assert findings.list.call_args.args[1:] == (
        review_id,
        FindingSeverity.HIGH,
        FindingCategory.SECURITY,
        FindingStatus.OPEN,
        FindingSource.AI,
        "app.py",
    )


def test_review_and_finding_responses_are_explicit(api):
    client, _, _, reviews, findings = api
    now = datetime.now(UTC)
    review_id = uuid4()
    finding_id = uuid4()
    reviews.list.return_value = paginated([
        ReviewResponse(
            id=review_id,
            pull_request_id=uuid4(),
            commit_sha="a" * 40,
            attempt_number=1,
            status=ReviewStatus.COMPLETED,
            overall_risk=ReviewRisk.HIGH,
            trigger_type="manual",
            model_name=None,
            model_version=None,
            prompt_version=None,
            duration_ms=None,
            static_analysis_duration_ms=None,
            ai_analysis_duration_ms=None,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            estimated_cost_usd=None,
            error_code=None,
            error_message=None,
            started_at=now,
            completed_at=now,
            findings_count=1,
            high_severity_findings_count=1,
            created_at=now,
            updated_at=now,
        )
    ], 1, PageParams())
    findings.get.return_value = ReviewFindingResponse(
        id=finding_id,
        review_id=review_id,
        file_path="app.py",
        start_line=1,
        end_line=2,
        diff_side="right",
        severity="high",
        category="security",
        title="Unsafe query",
        problem="Query is built from input.",
        explanation=None,
        suggestion=None,
        confidence="0.9500",
        source="ai",
        fingerprint="f" * 64,
        code_snippet=None,
        status="open",
        github_comment_id=None,
        published_to_github=False,
        created_at=now,
        updated_at=now,
    )
    review_response = client.get("/api/v1/reviews")
    finding_response = client.get(f"/api/v1/review-findings/{finding_id}")
    assert review_response.status_code == 200
    assert review_response.json()["items"][0]["findings_count"] == 1
    assert "github_token" not in review_response.text
    assert finding_response.status_code == 200
    assert finding_response.json()["fingerprint"] == "f" * 64


def test_database_failure_is_safe_and_rolls_back(caplog):
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id=uuid4(), github_user_id=1, github_login="test", display_name=None, email=None, avatar_url=None, profile_url=None, session_expires_at=datetime.now(UTC))
    session = AsyncMock()
    session.add = Mock()
    session.add = Mock()
    session.execute.side_effect = SQLAlchemyError("private database details")
    async def db():
        yield session
    app.dependency_overrides[get_db_session] = db
    with TestClient(app) as client:
        response = client.get("/api/v1/repositories")
    assert response.status_code == 503
    assert response.json() == {"detail": "Data is temporarily unavailable."}
    assert "private database details" not in response.text + caplog.text
    session.rollback.assert_awaited_once()


def test_dashboard_uses_counts_and_honest_zeros():
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id=uuid4(), github_user_id=1, github_login="test", display_name=None, email=None, avatar_url=None, profile_url=None, session_expires_at=datetime.now(UTC))
    session = AsyncMock()
    connected, counts, reviews, findings, total, rows = Mock(), Mock(), Mock(), Mock(), Mock(), Mock()
    connected.scalar_one.return_value = 1
    counts.one.return_value = (3, 1, 1, 1)
    reviews.one.return_value = (2, 1, 1, 0)
    findings.one.return_value = (5, 2)
    total.scalar_one.return_value = 3
    rows.all.return_value = []
    session.execute.side_effect = [connected, counts, reviews, findings, total, rows]
    async def db():
        yield session
    app.dependency_overrides[get_db_session] = db
    with TestClient(app) as client:
        response = client.get("/api/v1/dashboard/statistics")
    assert response.status_code == 200
    assert response.json() == {
        "connected_repository_count": 1, "total_pull_request_count": 3,
        "open_pr_count": 1, "closed_pr_count": 1, "merged_pr_count": 1,
        "total_reviews": 2, "completed_reviews": 1,
        "failed_reviews": 1, "in_progress_reviews": 0,
        "total_findings": 5, "high_severity_findings": 2,
        "reviews_count": 2, "findings_count": 5, "high_severity_findings_count": 2,
        "recently_updated_pull_requests": [],
    }


@pytest.mark.parametrize("kind", ["repository", "pull_request"])
def test_list_queries_apply_filters_order_and_bounded_pagination(kind):
    session = AsyncMock()
    count, rows = Mock(), Mock()
    count.scalar_one.return_value = 23
    rows.all.return_value = []
    session.execute.side_effect = [count, rows]
    pagination = PageParams(page=3, page_size=10)
    if kind == "repository":
        response = asyncio.run(RepositoryStore(session).list(pagination, "a%b_", False))
    else:
        response = asyncio.run(PullRequestStore(session).list(pagination, "a%b_", uuid4(), PullRequestStatus.OPEN))
    assert response.total_pages == 3 and response.page == 3
    statement = session.execute.call_args_list[1].args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert "ORDER BY" in sql and "LIMIT" in sql and "OFFSET" in sql
    assert "a/%b/_" in compiled.params.values()
    assert "a%b_" not in sql
    assert len(session.execute.call_args_list) == 2
    if kind == "repository":
        assert "GROUP BY pull_requests.repository_id" in sql
        assert "repositories.is_active = false" in sql
    else:
        assert "pull_requests.repository_id =" in sql and "pull_requests.status =" in sql
        assert "JOIN repositories" in sql


def test_pr_detail_serializes_joined_repository():
    from app.schemas.github import GitHubPullRequest, GitHubRepository
    from tests.github_fixtures import pr_payload, repository_payload
    now = datetime.now(UTC)
    repo = Repository(id=uuid4(), **GitHubRepository.model_validate(repository_payload()).model_dump())
    pr = PullRequest(id=uuid4(), repository_id=repo.id, **GitHubPullRequest.model_validate(pr_payload()).model_dump(),
                     created_at=now, updated_at=now, last_synced_at=now)
    session = AsyncMock()
    session.execute.return_value.one_or_none = Mock(return_value=(pr, repo))
    response = asyncio.run(PullRequestStore(session).get(pr.id))
    assert response.repository.id == repo.id
    assert response.repository_full_name == "octocat/example"
    assert response.changed_files == 3


@pytest.mark.parametrize("kind", ["review", "finding"])
def test_review_queries_apply_filters_order_and_bounded_pagination(kind):
    session = AsyncMock()
    count, rows = Mock(), Mock()
    count.scalar_one.return_value = 11
    rows.all.return_value = []
    rows.scalars.return_value.all.return_value = []
    session.execute.side_effect = [count, rows]
    pagination = PageParams(page=2, page_size=5)
    if kind == "review":
        response = asyncio.run(ReviewStore(session).list(pagination, uuid4(), uuid4(), ReviewStatus.COMPLETED, ReviewRisk.HIGH, "a" * 40))
    else:
        response = asyncio.run(ReviewFindingStore(session).list(
            pagination, uuid4(), FindingSeverity.HIGH, FindingCategory.SECURITY, FindingStatus.OPEN, FindingSource.AI, "a%b_"
        ))
    assert response.total_pages == 3 and response.page == 2
    statement = session.execute.call_args_list[1].args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert "ORDER BY" in sql and "LIMIT" in sql and "OFFSET" in sql
    if kind == "review":
        assert "JOIN pull_requests" in sql and "reviews.commit_sha =" in sql
    else:
        assert "review_findings.severity =" in sql and "review_findings.file_path" in sql
        assert "a/%b/_" in compiled.params.values()


def test_review_list_includes_related_pull_request_summary():
    now = datetime.now(UTC)
    repository = Repository(
        id=uuid4(),
        github_repository_id=1,
        owner="octocat",
        name="example",
        full_name="octocat/example",
        created_at=now,
        updated_at=now,
    )
    pull_request = PullRequest(
        id=uuid4(),
        repository_id=repository.id,
        github_pr_number=7,
        title="A real review",
        author_login="octocat",
        base_branch="main",
        head_branch="feature",
        status=PullRequestStatus.OPEN,
        head_sha="a" * 40,
        created_at=now,
        updated_at=now,
    )
    review = Review(
        id=uuid4(),
        pull_request_id=pull_request.id,
        commit_sha="a" * 40,
        attempt_number=1,
        status=ReviewStatus.COMPLETED,
        overall_risk=ReviewRisk.HIGH,
        trigger_type=ReviewTriggerType.MANUAL,
        started_at=now,
        completed_at=now,
        created_at=now,
        updated_at=now,
    )
    session = AsyncMock()
    count, rows = Mock(), Mock()
    count.scalar_one.return_value = 1
    rows.all.return_value = [(review, pull_request, repository, 3, 1)]
    session.execute.side_effect = [count, rows]

    page = asyncio.run(ReviewStore(session).list(PageParams()))

    item = page.items[0]
    assert item.repository_id == repository.id
    assert item.repository_full_name == "octocat/example"
    assert item.pull_request_number == 7
    assert item.pull_request_title == "A real review"
    assert item.pull_request_status == PullRequestStatus.OPEN


def test_finding_create_uses_review_fingerprint_unique_key():
    from decimal import Decimal
    from app.schemas.review import ReviewFindingCreate

    session = AsyncMock()
    insert_result = Mock()
    insert_result.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = insert_result
    created = asyncio.run(ReviewFindingStore(session).create_idempotent([
        ReviewFindingCreate(
            review_id=uuid4(),
            file_path="app.py",
            severity=FindingSeverity.HIGH,
            category=FindingCategory.SECURITY,
            title="Unsafe query",
            problem="Query is built from input.",
            confidence=Decimal("0.9"),
            source=FindingSource.AI,
            fingerprint="f" * 64,
        )
    ]))
    assert created == 1
    sql = str(session.execute.call_args.args[0].compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (review_id, fingerprint) DO NOTHING" in sql
    session.flush.assert_awaited_once()


def test_review_create_and_mark_status_support_future_orchestration():
    from app.schemas.review import ReviewCreate, ReviewStatusUpdate

    session = AsyncMock()
    session.add = Mock()
    review_id = uuid4()
    pull_request_id = uuid4()
    created = asyncio.run(ReviewStore(session).create(ReviewCreate(
        pull_request_id=pull_request_id,
        commit_sha="a" * 40,
        trigger_type="manual",
    )))
    assert created.pull_request_id == pull_request_id
    assert created.status == ReviewStatus.QUEUED
    session.add.assert_called_once()
    session.flush.assert_awaited_once()

    record = Mock()
    record.status = ReviewStatus.QUEUED
    locked = Mock()
    locked.scalar_one_or_none.return_value = record
    session.execute.return_value = locked
    updated = asyncio.run(ReviewStore(session).mark_status(review_id, ReviewStatusUpdate(status=ReviewStatus.COMPLETED)))
    assert updated is record
    assert record.status == ReviewStatus.COMPLETED
    assert record.completed_at is not None


def test_review_database_failure_is_safe_and_rolls_back(caplog):
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id=uuid4(), github_user_id=1, github_login="test", display_name=None, email=None, avatar_url=None, profile_url=None, session_expires_at=datetime.now(UTC))
    session = AsyncMock()
    session.execute.side_effect = SQLAlchemyError("private review details")
    async def db():
        yield session
    app.dependency_overrides[get_db_session] = db
    with TestClient(app) as client:
        response = client.get("/api/v1/reviews")
    assert response.status_code == 503
    assert response.json() == {"detail": "Data is temporarily unavailable."}
    assert "private review details" not in response.text + caplog.text
    session.rollback.assert_awaited_once()


def test_no_public_sync_route():
    paths = create_app().openapi()["paths"]
    assert not any("sync" in path for path in paths)
