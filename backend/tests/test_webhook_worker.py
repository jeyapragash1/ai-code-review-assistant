import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.dialects import postgresql

from app.clients.github_app import GitHubAppClient
from app.core.config import Settings
from app.models import WebhookEvent, WebhookEventStatus
from app.services.github import webhook_processing as worker
from app.services.github.webhook_ingestion import SUPPORTED_EVENTS

NOW = datetime.now(UTC)


def result(value):
    r = Mock()
    r.scalar_one_or_none.return_value = value
    r.scalar_one.return_value = value
    return r


@pytest.mark.parametrize("event_type", sorted(SUPPORTED_EVENTS - {"ping"}))
def test_worker_processes_each_event_with_mocked_github_transport(event_type, monkeypatch):
    installation = SimpleNamespace(id=uuid4(), github_installation_id=10, is_active=True, suspended_at=None)
    repository = SimpleNamespace(id=uuid4(), github_repository_id=20)
    pr = SimpleNamespace(id=uuid4(), head_sha="a" * 40, status="open")
    lifecycle = event_type in {"installation", "installation_repositories"}
    event = WebhookEvent(id=uuid4(), github_delivery_id=str(uuid4()), event_name=event_type, action="opened",
        payload={"installation": {"id": 10}, "sender": {"id": 41, "login": "owner"}, "pull_request": {"head": {"sha": pr.head_sha}}},
        github_repository_id=None if lifecycle else 20, github_pr_number=1, received_at=NOW,
        status=WebhookEventStatus.RECEIVED, payload_hash="0" * 64)
    session = AsyncMock()
    session.get.return_value = event
    session.execute.side_effect = [result(installation)] + ([result(installation)] if lifecycle else
        [result(repository), result(repository)] + ([result(pr)] if event_type == "pull_request" else [])) + [result(None)]
    sync = AsyncMock()
    full_sync = AsyncMock()
    queue = AsyncMock()
    monkeypatch.setattr(worker, "synchronize", sync)
    monkeypatch.setattr(worker, "synchronize_installations", full_sync)
    monkeypatch.setattr(worker, "queue_review", queue)
    monkeypatch.setattr("app.repositories.github_installation.GitHubInstallationStore.upsert_access", AsyncMock())
    monkeypatch.setattr("app.clients.github_app.app_jwt", lambda *_: "synthetic-test-jwt")
    calls = []
    def transport(request):
        calls.append(request.url.path)
        if request.url.path == "/app/installations/10/access_tokens":
            return httpx.Response(201, json={"token": "synthetic_test_token", "expires_at": (NOW + timedelta(hours=1)).isoformat()})
        if request.url.path == "/installation/repositories":
            return httpx.Response(200, json={"total_count": 1, "repositories": [{"id": 20, "name": "repo", "full_name": "owner/repo", "owner": {"login": "owner"}, "private": True}]})
        raise AssertionError("Unexpected mock transport request")
    monkeypatch.setattr(worker, "GitHubAppClient", lambda s: GitHubAppClient(s, transport=httpx.MockTransport(transport)))
    asyncio.run(worker.process_webhook(session, SimpleNamespace(webhook_event_id=event.id, retry_count=1), Settings(_env_file=None)))
    assert event.status == WebhookEventStatus.COMPLETED
    if lifecycle:
        full_sync.assert_awaited_once()
        assert not calls
    else:
        sync.assert_awaited_once()
        assert calls == ["/app/installations/10/access_tokens", "/installation/repositories"]
    assert queue.await_count == (1 if event_type == "pull_request" else 0)
    insert_statement = session.execute.call_args_list[-1].args[0]
    compiled = insert_statement.compile(dialect=postgresql.dialect())
    assert "ON CONFLICT (github_delivery_id) DO NOTHING" in str(compiled)
    assert compiled.params["event_type"] == event_type
    assert "payload" not in compiled.params


@pytest.mark.parametrize("action", ["deleted", "suspend"])
def test_installation_removal_and_suspension_revoke_access_without_live_calls(action, monkeypatch):
    installation = SimpleNamespace(id=uuid4(), is_active=True, suspended_at=None)
    event = WebhookEvent(id=uuid4(), github_delivery_id=str(uuid4()), event_name="installation", action=action,
        payload={"installation": {"id": 10}}, received_at=NOW, status=WebhookEventStatus.RECEIVED, payload_hash="0" * 64)
    session = AsyncMock()
    session.get.return_value = event
    session.execute.side_effect = [result(installation), result(None), result(None)]
    monkeypatch.setattr(worker, "GitHubAppClient", Mock(side_effect=AssertionError("No network expected")))
    asyncio.run(worker.process_webhook(session, SimpleNamespace(webhook_event_id=event.id, retry_count=1), Settings(_env_file=None)))
    assert not installation.is_active
    revoke = session.execute.call_args_list[1].args[0].compile().params
    assert revoke["is_active"] is False and revoke["revoked_at"]
    assert event.status == WebhookEventStatus.COMPLETED


def test_unsigned_or_invalid_installation_records_cannot_be_processed():
    session = AsyncMock()
    session.get.return_value = WebhookEvent(payload={}, status=WebhookEventStatus.RECEIVED)
    with pytest.raises(ValueError, match="valid installation"):
        asyncio.run(worker.process_webhook(session, SimpleNamespace(webhook_event_id=uuid4()), Settings(_env_file=None)))
    session.execute.assert_not_awaited()
