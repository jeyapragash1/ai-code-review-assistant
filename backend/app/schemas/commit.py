from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repository_id: UUID
    repository_full_name: str
    sha: str
    title: str
    message: str | None
    author_name: str | None
    author_login: str | None
    committer_name: str | None
    committer_login: str | None
    authored_at: datetime | None
    committed_at: datetime | None
    html_url: str | None
    parent_count: int
    reference: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime