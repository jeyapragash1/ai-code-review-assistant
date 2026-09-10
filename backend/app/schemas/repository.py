from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RepositorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    html_url: str | None


class RepositoryResponse(RepositorySummary):
    github_repository_id: int
    owner: str
    name: str
    description: str | None
    default_branch: str
    primary_language: str | None
    is_private: bool | None
    is_active: bool
    pull_request_count: int = 0
    open_pull_request_count: int = 0
    github_updated_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
