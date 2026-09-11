from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FindingSeverity, PullRequest, PullRequestStatus, Repository, Review, ReviewFinding, ReviewStatus
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
    in_progress_statuses = (
        ReviewStatus.QUEUED,
        ReviewStatus.FETCHING,
        ReviewStatus.STATIC_ANALYSIS,
        ReviewStatus.AI_ANALYSIS,
        ReviewStatus.VALIDATING,
        ReviewStatus.PUBLISHING,
    )
    total_reviews, completed_reviews, failed_reviews, in_progress_reviews = (await session.execute(select(
        func.count(Review.id),
        func.count().filter(Review.status == ReviewStatus.COMPLETED),
        func.count().filter(Review.status == ReviewStatus.FAILED),
        func.count().filter(Review.status.in_(in_progress_statuses)),
    ))).one()
    findings_count, high_findings_count = (await session.execute(select(
        func.count(ReviewFinding.id),
        func.count().filter(ReviewFinding.severity == FindingSeverity.HIGH),
    ))).one()
    recent = await PullRequestStore(session).list(PageParams(page_size=5))
    return DashboardStatistics(connected_repository_count=connected, total_pull_request_count=total,
                               open_pr_count=opened, closed_pr_count=closed, merged_pr_count=merged,
                               total_reviews=total_reviews, completed_reviews=completed_reviews,
                               failed_reviews=failed_reviews, in_progress_reviews=in_progress_reviews,
                               total_findings=findings_count, high_severity_findings=high_findings_count,
                               reviews_count=total_reviews, findings_count=findings_count,
                               high_severity_findings_count=high_findings_count,
                               recently_updated_pull_requests=recent.items)
