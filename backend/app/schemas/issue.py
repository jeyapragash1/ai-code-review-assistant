from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repository_id: UUID
    repository_full_name: str
    github_issue_id: int
    github_issue_number: int
    title: str
    body: str | None
    state: str
    state_reason: str | None
    author_login: str | None
    author_github_id: int | None
    assignees: list
    labels: list
    is_locked: bool
    comment_count: int
    html_url: str
    github_created_at: datetime
    github_updated_at: datetime
    github_closed_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime