from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.read_dependencies import pull_request_store
from app.models.enums import PullRequestStatus
from app.repositories.pull_request import PullRequestStore
from app.schemas.pagination import Page, PageParams
from app.schemas.pull_request import PullRequestDetail, PullRequestResponse

router = APIRouter(prefix="/pull-requests", tags=["pull requests"])


@router.get("", response_model=Page[PullRequestResponse])
async def list_pull_requests(
    store: Annotated[PullRequestStore, Depends(pull_request_store)],
    pagination: Annotated[PageParams, Depends()],
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    repository_id: UUID | None = None,
    status: PullRequestStatus | None = None,
) -> Page[PullRequestResponse]:
    return await store.list(pagination, search, repository_id, status)


@router.get("/{pull_request_id}", response_model=PullRequestDetail)
async def pull_request_detail(pull_request_id: UUID, store: Annotated[PullRequestStore, Depends(pull_request_store)]) -> PullRequestDetail:
    record = await store.get(pull_request_id)
    if record is None:
        raise HTTPException(404, "Pull request not found.")
    return record
