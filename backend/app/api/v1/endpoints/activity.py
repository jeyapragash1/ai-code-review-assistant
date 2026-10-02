from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.access import accessible_repository_ids, owned_installation_ids
from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.read_dependencies import read_session
from app.models import ActivityEvent, GitHubInstallation, Repository
from app.schemas.auth import AuthenticatedUser
from app.schemas.pagination import Page, PageParams, paginated

router = APIRouter(tags=["activity"])


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    repository_id: UUID | None
    installation_id: UUID | None
    actor_github_id: int | None
    actor_login: str | None
    event_type: str
    event_action: str | None
    safe_metadata: dict
    event_at: datetime
    received_at: datetime
    processing_status: str
    retry_count: int
    error_message: str | None


@router.get("/activity", response_model=Page[ActivityResponse])
@router.get("/repositories/{repository_id}/activity", response_model=Page[ActivityResponse])
async def activity(
    session: Annotated[AsyncSession, Depends(read_session)],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    pagination: Annotated[PageParams, Depends()],
    repository_id: UUID | None = None,
    event_type: Annotated[str | None, Query(max_length=100)] = None,
    actor: Annotated[str | None, Query(max_length=255)] = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> Page[ActivityResponse]:
    if (since and since.tzinfo is None) or (until and until.tzinfo is None) or (since and until and since > until):
        raise HTTPException(422, "Use an ordered date range with timezone offsets.")
    authorized = accessible_repository_ids(user)
    if repository_id and (await session.scalar(select(Repository.id).where(Repository.id == repository_id, Repository.id.in_(authorized)))) is None:
        raise HTTPException(404, "Repository not found.")
    owned_installations = owned_installation_ids(user)
    filters = [ActivityEvent.installation_id.in_(owned_installations)]
    if repository_id:
        filters.append(ActivityEvent.repository_id == repository_id)
    if event_type:
        filters.append(ActivityEvent.event_type == event_type)
    if actor:
        filters.append(func.lower(ActivityEvent.actor_login) == actor.lower())
    if since:
        filters.append(ActivityEvent.event_at >= since)
    if until:
        filters.append(ActivityEvent.event_at <= until)
    total = await session.scalar(select(func.count()).select_from(ActivityEvent).where(*filters))
    rows = (await session.execute(select(ActivityEvent).where(*filters).order_by(ActivityEvent.event_at.desc(), ActivityEvent.id.desc())
        .offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size))).scalars().all()
    return paginated([ActivityResponse.model_validate(row) for row in rows], total, pagination)
