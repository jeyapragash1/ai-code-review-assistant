from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.access import accessible_repository_ids
from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.read_dependencies import read_session
from app.core.config import settings
from app.models import PullRequest, PullRequestStatus, ReviewJob
from app.schemas.auth import AuthenticatedUser
from app.services.jobs import queue_review

router = APIRouter(prefix="/pull-requests", tags=["review jobs"])


class ReviewJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    pull_request_id: UUID
    head_sha: str
    status: str
    retry_count: int
    review_id: UUID | None
    error_message: str | None
    completed_at: datetime | None


async def authorized_pr(session, user, pull_request_id):
    pr = (await session.execute(select(PullRequest).where(PullRequest.id == pull_request_id,
        PullRequest.repository_id.in_(accessible_repository_ids(user))).with_for_update())).scalar_one_or_none()
    if pr is None:
        raise HTTPException(404, "Pull Request not found.")
    return pr


@router.post("/{pull_request_id}/review-jobs", response_model=ReviewJobResponse, status_code=202)
async def enqueue_review(pull_request_id: UUID, request: Request,
    session: Annotated[AsyncSession, Depends(read_session)], user: Annotated[AuthenticatedUser, Depends(get_current_user)]):
    if request.headers.get("origin") != settings.frontend_url:
        raise HTTPException(403, "Request origin is not allowed.")
    pr = await authorized_pr(session, user, pull_request_id)
    if pr.status != PullRequestStatus.OPEN:
        raise HTTPException(409, "Only open Pull Requests can be reviewed.")
    job = await queue_review(session, pr)
    await session.commit()
    return ReviewJobResponse.model_validate(job)


@router.get("/{pull_request_id}/review-jobs", response_model=ReviewJobResponse | None)
async def review_job_status(pull_request_id: UUID,
    session: Annotated[AsyncSession, Depends(read_session)], user: Annotated[AuthenticatedUser, Depends(get_current_user)]):
    pr = await authorized_pr(session, user, pull_request_id)
    job = (await session.execute(select(ReviewJob).where(ReviewJob.pull_request_id == pr.id, ReviewJob.head_sha == pr.head_sha))).scalar_one_or_none()
    return ReviewJobResponse.model_validate(job) if job else None
