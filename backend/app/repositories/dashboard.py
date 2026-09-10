from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PullRequest, PullRequestStatus, Repository
from app.repositories.pull_request import PullRequestStore
from app.schemas.dashboard import DashboardStatistics
from app.schemas.pagination import PageParams


async def dashboard_statistics(session: AsyncSession) -> DashboardStatistics:
    connected = (await session.execute(select(func.count()).select_from(Repository).where(Repository.is_active.is_(True)))).scalar_one()
    total, opened, closed, merged = (await session.execute(select(
        func.count(PullRequest.id),
        func.count().filter(PullRequest.status == PullRequestStatus.OPEN),
        func.count().filter(PullRequest.status == PullRequestStatus.CLOSED),
        func.count().filter(PullRequest.status == PullRequestStatus.MERGED),
    ))).one()
    recent = await PullRequestStore(session).list(PageParams(page_size=5))
    return DashboardStatistics(connected_repository_count=connected, total_pull_request_count=total,
                               open_pr_count=opened, closed_pr_count=closed, merged_pr_count=merged,
                               recently_updated_pull_requests=recent.items)
