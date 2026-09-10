import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app.models import PullRequest, Repository
from app.repositories.pull_request import PullRequestStore
from app.repositories.repository import RepositoryStore
from app.schemas.github import GitHubPullRequest, GitHubRepository, RepositoryTarget
from app.services.github.repository_sync import synchronize
from tests.github_fixtures import pr_payload, repository_payload

NOW = datetime.now(UTC)


def result(value):
    response = Mock()
    response.scalar_one_or_none.return_value = value
    response.scalar_one.return_value = value
    return response


def test_repository_creation_uses_unique_github_id():
    record = Repository(id=uuid4())
    session = AsyncMock()
    session.execute.return_value = result(record)
    saved, created = asyncio.run(RepositoryStore(session).upsert(GitHubRepository.model_validate(repository_payload()), NOW))
    assert saved.id == record.id and created
    sql = str(session.execute.call_args.args[0].compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (github_repository_id) DO NOTHING" in sql


def test_repository_update_preserves_identity_installation_and_active_preference():
    data = GitHubRepository.model_validate(repository_payload())
    original_id = uuid4()
    record = Repository(id=original_id, **data.model_dump(), is_active=False, github_installation_id=22)
    session = AsyncMock()
    session.execute.side_effect = [result(None), result(record)]
    new_data = GitHubRepository.model_validate(repository_payload() | {"description": "Updated"})
    saved, created = asyncio.run(RepositoryStore(session).upsert(new_data, NOW))
    assert not created and saved.id == original_id
    assert saved.description == "Updated"
    assert saved.is_active is False and saved.github_installation_id == 22
    assert saved.last_synced_at == NOW


def test_pr_creation_uses_repository_number_unique_key():
    session = AsyncMock()
    session.execute.return_value = result(uuid4())
    outcome = asyncio.run(PullRequestStore(session).upsert(uuid4(), GitHubPullRequest.model_validate(pr_payload()), NOW))
    assert outcome == "created"
    sql = str(session.execute.call_args.args[0].compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (repository_id, github_pr_number) DO NOTHING" in sql


@pytest.mark.parametrize("changed", [False, True])
def test_pr_update_and_unchanged_preserve_uuid(changed):
    data = GitHubPullRequest.model_validate(pr_payload())
    original_id = uuid4()
    repository_id = uuid4()
    record = PullRequest(id=original_id, repository_id=repository_id, **data.model_dump())
    session = AsyncMock()
    session.execute.side_effect = [result(None), result(record)]
    incoming = GitHubPullRequest.model_validate(pr_payload(title="Changed") if changed else pr_payload())
    outcome = asyncio.run(PullRequestStore(session).upsert(repository_id, incoming, NOW))
    assert outcome == ("updated" if changed else "unchanged")
    assert record.id == original_id
    assert record.last_synced_at == NOW
    assert record.title == incoming.title


def test_stale_snapshot_does_not_overwrite_newer_pr():
    data = GitHubPullRequest.model_validate(pr_payload())
    record = PullRequest(id=uuid4(), repository_id=uuid4(), **data.model_dump())
    record.github_updated_at = NOW
    record.title = "Newer title"
    session = AsyncMock()
    session.execute.side_effect = [result(None), result(record)]
    assert asyncio.run(PullRequestStore(session).upsert(record.repository_id, data, NOW)) == "unchanged"
    assert record.title == "Newer title"


class TransactionSession:
    def __init__(self):
        self.execute = AsyncMock()
        self.committed = False
        self.rolled_back = False

    @asynccontextmanager
    async def begin(self):
        try:
            yield
            self.committed = True
        except BaseException:
            self.rolled_back = True
            raise


@pytest.mark.parametrize("fail", [False, True])
def test_sync_commits_once_or_rolls_back(monkeypatch, fail):
    client = AsyncMock()
    client.repository.return_value = GitHubRepository.model_validate(repository_payload())
    client.pull_requests.return_value = [GitHubPullRequest.model_validate(pr_payload(i)) for i in (1, 2, 3)]
    repository_upsert = AsyncMock(return_value=(Repository(id=uuid4()), True))
    pr_upsert = AsyncMock(side_effect=["created", SQLAlchemyError("sensitive internal failure")] if fail else ["created", "updated", "unchanged"])
    monkeypatch.setattr(RepositoryStore, "upsert", repository_upsert)
    monkeypatch.setattr(PullRequestStore, "upsert", pr_upsert)
    session = TransactionSession()
    call = synchronize(client, session, RepositoryTarget(owner="octocat", repo="example"))
    if fail:
        with pytest.raises(SQLAlchemyError):
            asyncio.run(call)
        assert session.rolled_back and not session.committed
    else:
        summary = asyncio.run(call)
        assert (summary.prs_created, summary.prs_updated, summary.prs_unchanged) == (1, 1, 1)
        assert summary.total_prs_processed == 3 and session.committed


def test_upstream_failure_never_starts_transaction():
    client = AsyncMock()
    client.pull_requests.side_effect = RuntimeError("upstream failed")
    session = TransactionSession()
    with pytest.raises(RuntimeError):
        asyncio.run(synchronize(client, session, RepositoryTarget(owner="octocat", repo="example")))
    session.execute.assert_not_awaited()
    assert not session.committed
