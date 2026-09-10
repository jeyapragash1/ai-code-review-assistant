import asyncio
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.cli.sync_repository import run
from app.core.config import Settings


@pytest.mark.parametrize("owner,repo", [("../bad", "example"), ("", "example"), ("octocat", "../bad")])
def test_cli_invalid_target_returns_safe_nonzero(owner, repo, capsys):
    assert asyncio.run(run(owner, repo)) == 1
    assert "Synchronization failed." in capsys.readouterr().out


def test_cli_database_failure_does_not_print_exception(monkeypatch, capsys):
    monkeypatch.setattr("app.core.config.settings", Settings(_env_file=None, GITHUB_TOKEN=""))
    monkeypatch.setattr("app.services.github.repository_sync.synchronize", AsyncMock(side_effect=SQLAlchemyError("private connection information")))
    assert asyncio.run(run("octocat", "example")) == 1
    output = capsys.readouterr().out
    assert "Synchronization failed." in output
    assert "private connection information" not in output
