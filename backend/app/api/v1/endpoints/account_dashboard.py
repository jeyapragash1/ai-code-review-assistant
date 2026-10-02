from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.access import accessible_repository_ids, owned_repository_ids
from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.read_dependencies import read_session
from app.models import ActivityEvent, GitHubCommit, GitHubInstallation, GitHubIssue, InstallationRepositoryAccess, PullRequest, Repository, Review, ReviewFinding, ReviewJob
from app.schemas.auth import AuthenticatedUser

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class AccountStatistics(BaseModel):
    since: datetime
    until: datetime
    counts: dict[str, int]
    findings_by_severity: dict[str, int]
    findings_by_category: dict[str, int]
    findings_by_repository: dict[str, int]
    recently_updated_repositories: list[dict]
    most_active_repositories: list[dict]
    recent_commits: list[dict]
    recent_activity: list[dict]
    activity_metric: str = "Synchronized commits plus captured webhook events in the selected date range."


@router.get("/account-statistics", response_model=AccountStatistics)
async def account_statistics(session: Annotated[AsyncSession, Depends(read_session)],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)], repository_id: UUID | None = None,
    since: datetime | None = None, until: datetime | None = None):
    until = until or datetime.now(UTC)
    since = since or until - timedelta(days=30)
    if not since.tzinfo or not until.tzinfo or since > until:
        raise HTTPException(422, "Use an ordered timezone-aware date range.")
    owned_ids = owned_repository_ids(user)
    ids = owned_ids if repository_id is None else select(Repository.id).where(Repository.id.in_(owned_ids), Repository.id == repository_id)
    active_ids = accessible_repository_ids(user)
    counts = {}
    async def count(name, model, *conditions):
        counts[name] = (await session.execute(select(func.count()).select_from(model).where(*conditions))).scalar_one()
    await count("repositories_total", Repository, Repository.id.in_(ids), Repository.id.in_(active_ids))
    for name, condition in [("repositories_public", Repository.is_private.is_(False)), ("repositories_private", Repository.is_private.is_(True)),
        ("repositories_fork", Repository.is_fork.is_(True)), ("repositories_archived", Repository.is_archived.is_(True))]:
        await count(name, Repository, Repository.id.in_(ids), Repository.id.in_(active_ids), condition)
    await count("repositories_inactive", Repository, Repository.id.in_(ids), ~Repository.id.in_(active_ids))
    pr_filter = [PullRequest.repository_id.in_(ids)]
    await count("pull_requests_total", PullRequest, *pr_filter)
    for state in ("open", "closed", "merged"):
        await count("pull_requests_" + state, PullRequest, *pr_filter, PullRequest.status == state)
    await count("pull_requests_draft", PullRequest, *pr_filter, PullRequest.status == "open", PullRequest.is_draft.is_(True))
    for state in (None, "open", "closed"):
        await count("issues_" + (state or "total"), GitHubIssue, GitHubIssue.repository_id.in_(ids), *([GitHubIssue.state == state] if state else []))
    commit_conditions = [GitHubCommit.repository_id.in_(ids), GitHubCommit.committed_at >= since, GitHubCommit.committed_at <= until]
    activity_conditions = [ActivityEvent.repository_id.in_(ids), ActivityEvent.event_at >= since, ActivityEvent.event_at <= until]
    await count("recent_commits", GitHubCommit, *commit_conditions)
    await count("captured_push_events", ActivityEvent, *activity_conditions, ActivityEvent.event_type == "push")
    await count("recent_activity", ActivityEvent, *activity_conditions)
    pr_ids = select(PullRequest.id).where(*pr_filter)
    review_ids = select(Review.id).where(Review.pull_request_id.in_(pr_ids))
    for state in ("queued", "processing", "completed", "failed", "retryable"):
        await count("review_jobs_" + state, ReviewJob, ReviewJob.pull_request_id.in_(pr_ids), ReviewJob.status == state)
    await count("reviews_completed", Review, Review.pull_request_id.in_(pr_ids), Review.status == "completed")
    await count("findings_total", ReviewFinding, ReviewFinding.review_id.in_(review_ids))
    await count("findings_high", ReviewFinding, ReviewFinding.review_id.in_(review_ids), ReviewFinding.severity == "high")
    async def grouped(column):
        rows = (await session.execute(select(column, func.count()).select_from(ReviewFinding).join(Review).join(PullRequest)
            .where(PullRequest.repository_id.in_(ids)).group_by(column))).all()
        return {str(key): total for key, total in rows}
    severity, category, by_repo = await grouped(ReviewFinding.severity), await grouped(ReviewFinding.category), await grouped(PullRequest.repository_id)
    recent_repos = (await session.execute(select(Repository.id, Repository.full_name, Repository.github_updated_at, Repository.github_pushed_at,
        Repository.last_synced_at).where(Repository.id.in_(ids)).order_by(Repository.github_updated_at.desc().nullslast(), Repository.id).limit(5))).mappings().all()
    activity_union = union_all(select(GitHubCommit.repository_id).where(*commit_conditions), select(ActivityEvent.repository_id).where(*activity_conditions)).subquery()
    most_active = (await session.execute(select(Repository.id, Repository.full_name, func.count().label("activity_count")).join(activity_union, Repository.id == activity_union.c.repository_id)
        .group_by(Repository.id, Repository.full_name).order_by(func.count().desc(), Repository.id).limit(5))).mappings().all()
    commits = (await session.execute(select(GitHubCommit.id, GitHubCommit.repository_id, GitHubCommit.sha, GitHubCommit.title, GitHubCommit.committed_at)
        .where(*commit_conditions).order_by(GitHubCommit.committed_at.desc(), GitHubCommit.id.desc()).limit(5))).mappings().all()
    events = (await session.execute(select(ActivityEvent.id, ActivityEvent.repository_id, ActivityEvent.event_type, ActivityEvent.actor_login, ActivityEvent.event_at)
        .where(*activity_conditions).order_by(ActivityEvent.event_at.desc(), ActivityEvent.id.desc()).limit(5))).mappings().all()
    return AccountStatistics(since=since, until=until, counts=counts, findings_by_severity=severity, findings_by_category=category,
        findings_by_repository=by_repo, recently_updated_repositories=[dict(r) for r in recent_repos], most_active_repositories=[dict(r) for r in most_active],
        recent_commits=[dict(r) for r in commits], recent_activity=[dict(r) for r in events])
