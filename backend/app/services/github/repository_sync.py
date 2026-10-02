from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.github import GitHubClient
from app.repositories.pull_request import PullRequestStore
from app.repositories.repository import RepositoryStore
from app.repositories.issue import IssueStore
from app.repositories.commit import CommitStore
from app.schemas.github import RepositoryTarget


class SyncSummary(BaseModel):
    repository: Literal["created", "updated"]
    prs_created: int
    prs_updated: int
    prs_unchanged: int
    total_prs_processed: int
    synchronized_at: datetime


async def synchronize(client: GitHubClient, session: AsyncSession, target: RepositoryTarget) -> SyncSummary:
    metadata = await client.repository(target)
    prs = await client.pull_requests(target)
    issues = await client.issues(target)
    commits = await client.commits(target, client._settings.github_initial_commit_limit)
    counts = {"created": 0, "updated": 0, "unchanged": 0}
    # No transaction/locks are held during network I/O. Serialize writers for this GitHub ID.
    async with session.begin():
        await session.execute(select(func.pg_advisory_xact_lock(metadata.github_repository_id)))
        synced_at = datetime.now(UTC)
        repository, created = await RepositoryStore(session).upsert(metadata, synced_at)
        store = PullRequestStore(session)
        for pr in prs:
            outcome = await store.upsert(repository.id, pr, synced_at)
            counts[outcome] += 1
        issue_store = IssueStore(session)
        for issue in issues:
            await issue_store.upsert(repository.id, issue, synced_at)
        commit_store = CommitStore(session)
        for commit in commits:
            await commit_store.upsert(repository.id, commit, synced_at, metadata.default_branch)
    return SyncSummary(repository="created" if created else "updated", prs_created=counts["created"],
                       prs_updated=counts["updated"], prs_unchanged=counts["unchanged"],
                       total_prs_processed=len(prs), synchronized_at=synced_at)
