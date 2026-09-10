from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import PullRequestStatus
from app.schemas.repository import RepositorySummary


class PullRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    repository_id: UUID
    repository_full_name: str = ""
    github_pr_number: int
    title: str
    author_login: str
    base_branch: str
    head_branch: str
    status: PullRequestStatus
    is_draft: bool | None
    head_sha: str
    html_url: str | None
    additions: int | None
    deletions: int | None
    changed_files: int | None
    github_created_at: datetime | None
    github_updated_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PullRequestDetail(PullRequestResponse):
    repository: RepositorySummary
