import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.read_dependencies import pull_request_store, repository_store
from app.db.session import get_db_session
from app.main import create_app
from app.models import PullRequest, PullRequestStatus, Repository
from app.repositories.pull_request import PullRequestStore
from app.repositories.repository import RepositoryStore
from app.schemas.pagination import PageParams, paginated
from app.schemas.repository import RepositoryResponse


@pytest.fixture
def api():
    app = create_app()
    repo_store = AsyncMock()
    pr_store = AsyncMock()
    repo_store.list.return_value = paginated([], 0, PageParams())
    pr_store.list.return_value = paginated([], 0, PageParams())
    repo_store.get.return_value = None
    pr_store.get.return_value = None
    app.dependency_overrides[repository_store] = lambda: repo_store
    app.dependency_overrides[pull_request_store] = lambda: pr_store
    with TestClient(app) as client:
        yield client, repo_store, pr_store


@pytest.mark.parametrize("path", [
    "/repositories?page=0", "/repositories?page_size=101", "/repositories?page_size=0",
    "/repositories?page=foo", "/repositories?is_active=maybe", "/repositories?search=",
    "/pull-requests?status=unknown", "/pull-requests?repository_id=invalid", "/pull-requests?page=-1",
    "/repositories/not-a-uuid", "/pull-requests/not-a-uuid", "/repositories?search=" + "x" * 201,
])
def test_query_and_uuid_validation(api, path):
    client, _, _ = api
    assert client.get("/api/v1" + path).status_code == 422


def test_repository_filters_are_forwarded(api):
    client, repos, _ = api
    response = client.get("/api/v1/repositories?page=2&page_size=5&search=example&is_active=false")
    assert response.status_code == 200
    args = repos.list.call_args.args
    assert args[0] == PageParams(page=2, page_size=5)
    assert args[1:] == ("example", False)
    assert set(response.json()) == {"items", "total", "page", "page_size", "total_pages"}


def test_pr_filters_are_forwarded(api):
    client, _, prs = api
    repo_id = uuid4()
    response = client.get(f"/api/v1/pull-requests?repository_id={repo_id}&search=fix&status=merged")
    assert response.status_code == 200
    assert prs.list.call_args.args[1:] == ("fix", repo_id, PullRequestStatus.MERGED)


@pytest.mark.parametrize("path", ["/repositories/", "/pull-requests/"])
def test_missing_record_404(api, path):
    assert api[0].get("/api/v1" + path + str(uuid4())).status_code == 404


def test_nested_pr_endpoint_checks_repository(api):
    client, repos, prs = api
    repo_id = uuid4()
    assert client.get(f"/api/v1/repositories/{repo_id}/pull-requests").status_code == 404
    prs.list.assert_not_awaited()
    repos.get.return_value = Mock()
    response = client.get(f"/api/v1/repositories/{repo_id}/pull-requests?status=open&page_size=10")
    assert response.status_code == 200
    assert prs.list.call_args.kwargs == {"repository_id": repo_id, "status": PullRequestStatus.OPEN}


def test_repository_response_is_explicit(api):
    client, repos, _ = api
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


def test_database_failure_is_safe_and_rolls_back(caplog):
    app = create_app()
    session = AsyncMock()
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
    session = AsyncMock()
    connected, counts, total, rows = Mock(), Mock(), Mock(), Mock()
    connected.scalar_one.return_value = 1
    counts.one.return_value = (3, 1, 1, 1)
    total.scalar_one.return_value = 3
    rows.all.return_value = []
    session.execute.side_effect = [connected, counts, total, rows]
    async def db():
        yield session
    app.dependency_overrides[get_db_session] = db
    with TestClient(app) as client:
        response = client.get("/api/v1/dashboard/statistics")
    assert response.status_code == 200
    assert response.json() == {
        "connected_repository_count": 1, "total_pull_request_count": 3,
        "open_pr_count": 1, "closed_pr_count": 1, "merged_pr_count": 1,
        "reviews_count": 0, "findings_count": 0, "high_severity_findings_count": 0,
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


def test_no_public_sync_route():
    paths = create_app().openapi()["paths"]
    assert not any("sync" in path for path in paths)
