import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.core.config import Settings
from app.services.github import installation_sync


def test_successful_listing_reconciles_missing_installations_within_user_scope(monkeypatch):
    client = SimpleNamespace(installations=AsyncMock(return_value=[]))
    context = AsyncMock()
    context.__aenter__.return_value = client
    monkeypatch.setattr(installation_sync, "GitHubAppClient", lambda _: context)
    installation = SimpleNamespace(id=uuid4(), is_active=True, last_synced_at=None)
    rows = Mock()
    rows.scalars.return_value.all.return_value = [installation]
    session = AsyncMock()
    session.begin = Mock(return_value=AsyncMock())
    session.execute.return_value = rows
    revoke = AsyncMock()
    monkeypatch.setattr(installation_sync.GitHubInstallationStore, "revoke_missing", revoke)
    result = asyncio.run(installation_sync._synchronize_installations(Settings(_env_file=None), session, 41, {10}))
    assert result.installations_processed == 0
    assert installation.is_active is False
    revoke.assert_awaited_once()
    sql = str(session.execute.call_args.args[0])
    assert "account_github_id" in sql and "github_installation_id" in sql
    assert "FOR UPDATE" in sql
