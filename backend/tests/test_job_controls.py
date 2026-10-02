import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.read_dependencies import read_session
from app.db.session import get_db_session
from app.main import create_app
from app.models import ReviewJob
from app.schemas.auth import AuthenticatedUser
from app.services import job_worker

NOW = datetime.now(UTC)
USER = AuthenticatedUser(id=uuid4(), github_user_id=41, github_login="owner", display_name=None, email=None,
    avatar_url=None, profile_url=None, session_expires_at=NOW + timedelta(hours=1))


def result(value):
    r = Mock()
    r.scalar_one_or_none.return_value = value
    r.scalar_one.return_value = value
    return r


@pytest.mark.parametrize("mode", ["locked", "completed", "failed", "timeout"])
def test_review_worker_locking_safe_failure_and_timeout(mode, monkeypatch):
    job = ReviewJob(id=uuid4(), pull_request_id=uuid4(), head_sha="a" * 40, trigger_type="webhook", status="processing",
        retry_count=1, lease_token=uuid4(), lease_until=NOW + timedelta(minutes=5), available_at=NOW)
    session = AsyncMock()
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session
    monkeypatch.setattr(job_worker, "AsyncSessionLocal", lambda: session_context)
    monkeypatch.setattr(job_worker, "claim_job", AsyncMock(return_value=job))
    connection = AsyncMock()
    connection.execute.side_effect = [result(mode != "locked"), result(None)]
    lock_context = AsyncMock()
    lock_context.__aenter__.return_value = connection
    monkeypatch.setattr(job_worker, "engine", SimpleNamespace(connect=lambda: lock_context))
    finish = AsyncMock()
    monkeypatch.setattr(job_worker, "finish_job", finish)
    processor = AsyncMock(return_value=SimpleNamespace(review_id=uuid4()))
    if mode == "failed":
        processor.side_effect = RuntimeError("private transport detail")
    elif mode == "timeout":
        async def delay(*_):
            await asyncio.sleep(10)
        processor.side_effect = delay
        monkeypatch.setattr(job_worker.settings, "job_timeout_seconds", 0.001)
    monkeypatch.setattr(job_worker, "process_review", processor)
    assert asyncio.run(job_worker.run_once(ReviewJob))
    if mode == "locked":
        processor.assert_not_awaited()
    else:
        processor.assert_awaited_once()
        assert "pg_advisory_unlock" in str(connection.execute.call_args.args[0])
    assert finish.call_args.kwargs.get("error", False) == (mode != "completed")


def test_manual_review_queue_endpoint_is_repeatable_and_scoped(monkeypatch):
    from app.api.v1.endpoints import review_jobs
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: USER
    session = AsyncMock()
    pr = SimpleNamespace(id=uuid4(), status="open", head_sha="a" * 40)
    session.execute.return_value = result(pr)
    async def db():
        yield session
    app.dependency_overrides[read_session] = db
    job = ReviewJob(id=uuid4(), pull_request_id=pr.id, head_sha=pr.head_sha, status="queued", retry_count=0)
    monkeypatch.setattr(review_jobs, "queue_review", AsyncMock(return_value=job))
    path = f"/api/v1/pull-requests/{pr.id}/review-jobs"
    with TestClient(app) as client:
        first = client.post(path, headers={"Origin": "http://localhost:3000"})
        second = client.post(path, headers={"Origin": "http://localhost:3000"})
    assert first.status_code == second.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert "account_github_id" in str(session.execute.call_args.args[0])
    assert "user_repository_access.user_id" in str(session.execute.call_args.args[0])


@pytest.mark.parametrize("missing,status", [(True, 404), (False, 409)])
def test_manual_review_cannot_queue_another_account_or_closed_pr(missing, status):
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: USER
    session = AsyncMock()
    session.execute.return_value = result(None if missing else SimpleNamespace(status="closed"))
    async def db():
        yield session
    app.dependency_overrides[read_session] = db
    with TestClient(app) as client:
        r = client.post(f"/api/v1/pull-requests/{uuid4()}/review-jobs", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == status
    session.commit.assert_not_awaited()


def test_sync_control_reports_readiness_and_safe_results(monkeypatch):
    from app.api.v1.endpoints import github
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: USER
    session = AsyncMock()
    results = [result(1), result(4), result(NOW), result(SimpleNamespace(status="partial", error_message="Some repositories could not be synchronized."))]
    session.execute.side_effect = results
    async def db():
        yield session
    app.dependency_overrides[get_db_session] = db
    with TestClient(app) as client:
        r = client.get("/api/v1/github/sync/status")
    assert r.status_code == 200
    assert r.json()["accessible_repository_count"] == 4
    assert r.json()["last_result"] == "partial"
    assert r.json()["app_configured"] is False
    assert "token" not in r.text and "private_key_path" not in r.text


def test_sync_endpoint_uses_authorized_installations_and_post(monkeypatch, tmp_path):
    from app.api.v1.endpoints import github
    from app.services.github.installation_sync import InstallationSyncSummary
    # Readiness only stats the file; no private key is read by mocked sync.
    key = tmp_path / "not_a_real_key.pem"
    key.write_text("synthetic readiness fixture", encoding="utf-8")
    monkeypatch.setattr(github.settings, "github_app_id", "test_app")
    monkeypatch.setattr(github.settings, "github_app_private_key_path", str(key))
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: USER
    session = AsyncMock()
    session.add = Mock()
    granted = Mock()
    granted.scalars.return_value.all.return_value = [10]
    session.execute.return_value = granted
    async def db():
        yield session
    app.dependency_overrides[get_db_session] = db
    summary = InstallationSyncSummary(installations_processed=1, repositories_processed=4, repositories_failed=0,
        pull_requests_processed=2, synchronized_at=NOW)
    sync = AsyncMock(return_value=summary)
    monkeypatch.setattr(github, "synchronize_installations", sync)
    with TestClient(app) as client:
        assert client.get("/api/v1/github/sync").status_code == 405
        response = client.post("/api/v1/github/sync", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 202 and response.json()["repositories_processed"] == 4
    assert sync.call_args.kwargs == {"account_github_id": USER.github_user_id, "granted_installation_ids": {10}}
    assert session.add.call_args.args[0].status == "completed"


def test_active_review_is_not_duplicated(monkeypatch):
    from app.services.static_analysis.review_runner import run_static_review, StaticReviewError
    from app.core.config import Settings
    class Session:
        def begin(self):
            return AsyncMock()
    pr = SimpleNamespace(id=uuid4(), head_sha="a" * 40)
    monkeypatch.setattr("app.repositories.review.ReviewStore.pull_request_with_repository", AsyncMock(return_value=(pr, SimpleNamespace())))
    monkeypatch.setattr("app.repositories.review.ReviewStore.completed_for_commit", AsyncMock(return_value=None))
    monkeypatch.setattr("app.repositories.review.ReviewStore.active_for_commit", AsyncMock(return_value=SimpleNamespace()))
    create = AsyncMock()
    monkeypatch.setattr("app.repositories.review.ReviewStore.create", create)
    with pytest.raises(StaticReviewError, match="already processing"):
        asyncio.run(run_static_review(client=AsyncMock(), session=Session(), settings=Settings(_env_file=None), pull_request_id=pr.id))
    create.assert_not_awaited()


def test_review_timeout_marks_failure_and_removes_temporary_files(monkeypatch):
    from app.services.static_analysis import review_runner as runner
    from app.core.config import Settings
    from app.models import ReviewStatus
    class Session:
        rollback = AsyncMock()
        def begin(self):
            return AsyncMock()
    pr = SimpleNamespace(id=uuid4(), head_sha="a" * 40)
    repo = SimpleNamespace(owner="owner", name="repo")
    review_id = uuid4()
    monkeypatch.setattr("app.repositories.review.ReviewStore.pull_request_with_repository", AsyncMock(return_value=(pr, repo)))
    monkeypatch.setattr("app.repositories.review.ReviewStore.completed_for_commit", AsyncMock(return_value=None))
    monkeypatch.setattr("app.repositories.review.ReviewStore.active_for_commit", AsyncMock(return_value=None))
    monkeypatch.setattr("app.repositories.review.ReviewStore.next_attempt_number", AsyncMock(return_value=1))
    monkeypatch.setattr("app.repositories.review.ReviewStore.create", AsyncMock(return_value=SimpleNamespace(id=review_id)))
    mark = AsyncMock()
    monkeypatch.setattr("app.repositories.review.ReviewStore.mark_status", mark)
    directories = []
    async def interrupted_download(client, target, pull_request, root, settings):
        directories.append(root)
        (root / "temporary-analysis-file.py").write_text("pass", encoding="utf-8")
        await asyncio.sleep(10)
    monkeypatch.setattr(runner, "_prepare_files", interrupted_download)
    async def invoke():
        async with asyncio.timeout(0.01):
            await runner.run_static_review(client=AsyncMock(), session=Session(), settings=Settings(_env_file=None), pull_request_id=pr.id)
    with pytest.raises(TimeoutError):
        asyncio.run(invoke())
    assert directories and all(not directory.exists() for directory in directories)
    assert mark.call_args.args[1].status == ReviewStatus.FAILED
    assert mark.call_args.args[1].error_code == "review_timeout"


def test_cancelled_analyzer_finishes_before_temporary_cleanup(monkeypatch, tmp_path):
    import time
    from app.services.static_analysis import subprocess as analyzer
    finished = []
    def trusted_subprocess(*args, **kwargs):
        time.sleep(0.02)
        finished.append(True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(analyzer.subprocess, "run", trusted_subprocess)
    async def invoke():
        async with asyncio.timeout(0.001):
            await analyzer.run_analyzer(["synthetic-trusted-analyzer"], tmp_path, 1)
    with pytest.raises(TimeoutError):
        asyncio.run(invoke())
    assert finished == [True]
