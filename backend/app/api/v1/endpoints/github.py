import asyncio
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.access import owned_installation_ids
from app.core.config import settings
from app.db.session import get_db_session
from app.models import GitHubInstallation, InstallationRepositoryAccess, GitHubSyncRun
from app.schemas.auth import AuthenticatedUser
from app.services.github.installation_sync import SynchronizationBusy, synchronize_installations

router = APIRouter(prefix="/github", tags=["github"], dependencies=[Depends(get_current_user)])
_sync_lock = asyncio.Lock()


class InstallationStatus(BaseModel):
    id: int
    account_login: str
    account_type: str
    repository_selection: str
    is_active: bool
    repository_count: int
    last_synced_at: datetime | None


class GitHubSyncStatus(BaseModel):
    app_configured: bool
    private_key_configured: bool
    installation_count: int
    accessible_repository_count: int
    last_synchronized_at: datetime | None
    last_result: str | None
    safe_error: str | None = None
    webhook_configured: bool = False


class GitHubSyncResponse(BaseModel):
    status: str
    installations_processed: int
    repositories_processed: int
    repositories_failed: int
    pull_requests_processed: int
    synchronized_at: datetime


@router.get("/installations", response_model=list[InstallationStatus])
async def list_installations(session: Annotated[AsyncSession, Depends(get_db_session)], user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> list[InstallationStatus]:
    rows = (await session.execute(select(GitHubInstallation).where(GitHubInstallation.id.in_(owned_installation_ids(user))).order_by(GitHubInstallation.account_login, GitHubInstallation.id))).scalars().all()
    result = []
    for installation in rows:
        count = (await session.execute(select(func.count()).select_from(InstallationRepositoryAccess).where(InstallationRepositoryAccess.installation_id == installation.id, InstallationRepositoryAccess.is_active.is_(True)))).scalar_one()
        result.append(InstallationStatus(id=installation.github_installation_id, account_login=installation.account_login, account_type=installation.account_type, repository_selection=installation.repository_selection, is_active=installation.is_active, repository_count=count, last_synced_at=installation.last_synced_at))
    return result


@router.get("/sync/status", response_model=GitHubSyncStatus)
async def sync_status(session: Annotated[AsyncSession, Depends(get_db_session)], user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> GitHubSyncStatus:
    owned = GitHubInstallation.id.in_(owned_installation_ids(user))
    installation_count = (await session.execute(select(func.count()).select_from(GitHubInstallation).where(owned, GitHubInstallation.is_active.is_(True)))).scalar_one()
    repository_count = (await session.execute(select(func.count(func.distinct(InstallationRepositoryAccess.repository_id))).join(GitHubInstallation).where(owned, GitHubInstallation.is_active.is_(True), InstallationRepositoryAccess.is_active.is_(True)))).scalar_one()
    last_sync = (await session.execute(select(func.max(GitHubInstallation.last_synced_at)).where(owned))).scalar_one()
    run = (await session.execute(select(GitHubSyncRun).where(GitHubSyncRun.user_id == user.id).order_by(GitHubSyncRun.created_at.desc(), GitHubSyncRun.id.desc()).limit(1))).scalar_one_or_none()
    return GitHubSyncStatus(app_configured=settings.github_app_configured, private_key_configured=bool(settings.github_app_private_key_path.strip()), installation_count=installation_count, accessible_repository_count=repository_count, last_synchronized_at=last_sync, last_result=run.status if run else None, safe_error=run.error_message if run else None, webhook_configured=bool(settings.github_webhook_secret.strip()))


@router.post("/sync", response_model=GitHubSyncResponse, status_code=202)
async def start_sync(session: Annotated[AsyncSession, Depends(get_db_session)], user: Annotated[AuthenticatedUser, Depends(get_current_user)], origin: Annotated[str | None, Header()] = None) -> GitHubSyncResponse:
    if origin != settings.frontend_url:
        raise HTTPException(403, "Request origin is not allowed.")
    if not settings.github_app_configured:
        raise HTTPException(503, "GitHub App synchronization is not configured.")
    if _sync_lock.locked():
        raise HTTPException(409, "GitHub synchronization is already running.")
    async with _sync_lock:
        granted_ids = set((await session.execute(select(GitHubInstallation.github_installation_id).where(
            GitHubInstallation.id.in_(owned_installation_ids(user))))).scalars().all())
        run = GitHubSyncRun(user_id=user.id, status="processing")
        session.add(run)
        await session.commit()
        run_id = run.id
        try:
            summary = await synchronize_installations(settings, session, account_github_id=user.github_user_id, granted_installation_ids=granted_ids)
            run.status = "completed" if not summary.repositories_failed else "partial"
            run.error_message = "Some repositories could not be synchronized." if summary.repositories_failed else None
            run.completed_at = datetime.now(UTC)
            await session.commit()
        except SynchronizationBusy:
            run.status = "failed"
            run.error_message = "GitHub synchronization is already running."
            await session.commit()
            raise HTTPException(409, "GitHub synchronization is already running.") from None
        except Exception:
            await session.rollback()
            await session.execute(update(GitHubSyncRun).where(GitHubSyncRun.id == run_id).values(
                status="failed", error_message="GitHub synchronization failed; check configuration and App permissions.",
                completed_at=datetime.now(UTC)))
            await session.commit()
            raise HTTPException(503, "GitHub synchronization failed.") from None
    return GitHubSyncResponse(status="completed", **summary.model_dump())
