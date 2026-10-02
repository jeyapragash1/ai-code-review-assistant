from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.github import GitHubClient
from app.clients.github_app import GitHubAppClient, GitHubInstallationSummary
from app.core.config import Settings
from app.models import GitHubInstallation, Repository
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


class SynchronizationBusy(Exception):
    pass


async def synchronize_installations(settings: Settings, session: AsyncSession, account_github_id: int | None = None, granted_installation_ids: set[int] | None = None) -> InstallationSyncSummary:
    from app.db.session import engine
    async with engine.connect() as lock_connection:
        acquired = (await lock_connection.execute(select(func.pg_try_advisory_lock(726438201)))).scalar_one()
        if not acquired:
            raise SynchronizationBusy("GitHub synchronization is already running.")
        try:
            return await _synchronize_installations(settings, session, account_github_id, granted_installation_ids)
        finally:
            await lock_connection.execute(select(func.pg_advisory_unlock(726438201)))
            await lock_connection.commit()


async def _synchronize_installations(settings: Settings, session: AsyncSession, account_github_id: int | None = None, granted_installation_ids: set[int] | None = None) -> InstallationSyncSummary:
    synced_at = datetime.now(UTC)
    repositories_processed = repositories_failed = pull_requests_processed = 0
    async with GitHubAppClient(settings) as app_client:
        installations = await app_client.installations()
        if account_github_id is not None:
            installations = [item for item in installations if item.account.get("id") == account_github_id or item.id in (granted_installation_ids or set())]
        for item in installations:
            installation_values = _installation_values(item)
            async with session.begin():
                installation = await GitHubInstallationStore(session).upsert(installation_values, synced_at)
                installation.is_active = item.suspended_at is None
            if item.suspended_at is not None:
                async with session.begin():
                    await GitHubInstallationStore(session).revoke_missing(installation.id, set(), synced_at)
                continue
            token = await app_client.installation_token(item.id)
            accessible = await app_client.installation_repositories(item.id)
            installation_id = installation.id
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
                    await GitHubInstallationStore(session).upsert_access(installation_id, repository.id, synced_at)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    # A temporary API failure is not evidence that access was revoked.
                    prior = (await session.execute(select(Repository.id).where(Repository.github_repository_id == accessible_repo.id))).scalar_one_or_none()
                    if prior:
                        seen_ids.add(prior)
                    await session.commit()
                    repositories_failed += 1
            async with session.begin():
                await GitHubInstallationStore(session).revoke_missing(installation_id, seen_ids, synced_at)
        # A successful authoritative installation listing can also reconcile
        # missed removal webhooks. Restrict reconciliation to the caller's scope.
        conditions = [GitHubInstallation.is_active.is_(True),
            GitHubInstallation.github_installation_id.notin_({item.id for item in installations})]
        if account_github_id is not None:
            conditions.append(or_(GitHubInstallation.account_github_id == account_github_id,
                GitHubInstallation.github_installation_id.in_(granted_installation_ids or set())))
        async with session.begin():
            missing = (await session.execute(select(GitHubInstallation).where(*conditions).with_for_update())).scalars().all()
            for installation in missing:
                installation.is_active = False
                installation.last_synced_at = synced_at
                await GitHubInstallationStore(session).revoke_missing(installation.id, set(), synced_at)
    return InstallationSyncSummary(installations_processed=len(installations), repositories_processed=repositories_processed, repositories_failed=repositories_failed, pull_requests_processed=pull_requests_processed, synchronized_at=synced_at)
