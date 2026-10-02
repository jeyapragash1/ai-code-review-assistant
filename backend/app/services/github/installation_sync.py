from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.github import GitHubClient
from app.clients.github_app import GitHubAppClient, GitHubInstallationSummary
from app.core.config import Settings
from app.models import Repository
from app.repositories.github_installation import GitHubInstallationStore
from app.schemas.github import RepositoryTarget
from app.services.github.repository_sync import synchronize


class InstallationSyncSummary(BaseModel):
    installations_processed: int
    repositories_processed: int
    repositories_failed: int
    pull_requests_processed: int
    synchronized_at: datetime


def _account_value(account: dict, key: str, default: object = None) -> object:
    value = account.get(key, default)
    return value


def _installation_values(item: GitHubInstallationSummary) -> dict:
    account = item.account
    account_id = _account_value(account, "id")
    login = _account_value(account, "login")
    account_type = _account_value(account, "type", "Unknown")
    if not isinstance(account_id, int) or account_id <= 0 or not isinstance(login, str) or not login or not isinstance(account_type, str):
        raise ValueError("invalid GitHub installation account")
    return {
        "github_installation_id": item.id,
        "account_github_id": account_id,
        "account_login": login,
        "account_type": account_type,
        "repository_selection": item.repository_selection,
        "permissions": item.permissions,
        "events": item.events,
        "suspended_at": item.suspended_at,
        "github_created_at": item.created_at,
        "github_updated_at": item.updated_at,
    }


async def synchronize_installations(settings: Settings, session: AsyncSession) -> InstallationSyncSummary:
    synced_at = datetime.now(UTC)
    repositories_processed = repositories_failed = pull_requests_processed = 0
    async with GitHubAppClient(settings) as app_client:
        installations = await app_client.installations()
        for item in installations:
            installation_values = _installation_values(item)
            async with session.begin():
                installation = await GitHubInstallationStore(session).upsert(installation_values, synced_at)
            token = await app_client.installation_token(item.id)
            accessible = await app_client.installation_repositories(item.id)
            seen_ids = set()
            for accessible_repo in accessible:
                target = RepositoryTarget(owner=str(accessible_repo.owner.get("login", "")), repo=accessible_repo.name)
                try:
                    async with GitHubClient(settings, access_token=token.value) as client:
                        summary = await synchronize(client, session, target)
                    repositories_processed += 1
                    pull_requests_processed += summary.total_prs_processed
                    repository = (await session.execute(select(Repository).where(Repository.github_repository_id == accessible_repo.id))).scalar_one()
                    seen_ids.add(repository.id)
                    await GitHubInstallationStore(session).upsert_access(installation.id, repository.id, synced_at)
                    await session.commit()
                except Exception:
                    repositories_failed += 1
            async with session.begin():
                await GitHubInstallationStore(session).revoke_missing(installation.id, seen_ids, synced_at)
    return InstallationSyncSummary(installations_processed=len(installations), repositories_processed=repositories_processed, repositories_failed=repositories_failed, pull_requests_processed=pull_requests_processed, synchronized_at=synced_at)