from pydantic import BaseModel

from app.schemas.pull_request import PullRequestResponse


class DashboardStatistics(BaseModel):
    connected_repository_count: int
    total_pull_request_count: int
    open_pr_count: int
    closed_pr_count: int
    merged_pr_count: int
    total_reviews: int
    completed_reviews: int
    failed_reviews: int
    in_progress_reviews: int
    total_findings: int
    high_severity_findings: int
    reviews_count: int
    findings_count: int
    high_severity_findings_count: int
    recently_updated_pull_requests: list[PullRequestResponse]
