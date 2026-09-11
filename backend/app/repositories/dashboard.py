from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FindingSeverity, PullRequest, PullRequestStatus, Repository, Review, ReviewFinding
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
    reviews_count = (await session.execute(select(func.count()).select_from(Review))).scalar_one()
    findings_count, high_findings_count = (await session.execute(select(
        func.count(ReviewFinding.id),
        func.count().filter(ReviewFinding.severity == FindingSeverity.HIGH),
    ))).one()
    recent = await PullRequestStore(session).list(PageParams(page_size=5))
    return DashboardStatistics(connected_repository_count=connected, total_pull_request_count=total,
                               open_pr_count=opened, closed_pr_count=closed, merged_pr_count=merged,
                               reviews_count=reviews_count, findings_count=findings_count,
                               high_severity_findings_count=high_findings_count,
                               recently_updated_pull_requests=recent.items)
