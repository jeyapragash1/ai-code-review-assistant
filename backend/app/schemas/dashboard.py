from typing import Literal

from pydantic import BaseModel

from app.schemas.pull_request import PullRequestResponse


class DashboardStatistics(BaseModel):
    connected_repository_count: int
    total_pull_request_count: int
    open_pr_count: int
    closed_pr_count: int
    merged_pr_count: int
    reviews_count: Literal[0] = 0
    findings_count: Literal[0] = 0
    high_severity_findings_count: Literal[0] = 0
    recently_updated_pull_requests: list[PullRequestResponse]
