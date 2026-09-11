from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.read_dependencies import pull_request_store, repository_store
from app.models.enums import PullRequestStatus
from app.repositories.pull_request import PullRequestStore
from app.repositories.repository import RepositoryStore
from app.schemas.pagination import Page, PageParams
from app.schemas.pull_request import PullRequestResponse
from app.schemas.repository import RepositoryResponse
from app.api.v1.auth_dependencies import get_current_user

router = APIRouter(prefix="/repositories", tags=["repositories"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=Page[RepositoryResponse])
async def list_repositories(
    store: Annotated[RepositoryStore, Depends(repository_store)],
    pagination: Annotated[PageParams, Depends()],
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    is_active: bool | None = None,
) -> Page[RepositoryResponse]:
    return await store.list(pagination, search, is_active)


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def repository_detail(repository_id: UUID, store: Annotated[RepositoryStore, Depends(repository_store)]) -> RepositoryResponse:
    record = await store.get(repository_id)
    if record is None:
        raise HTTPException(404, "Repository not found.")
    return record


@router.get("/{repository_id}/pull-requests", response_model=Page[PullRequestResponse])
async def repository_pull_requests(
    repository_id: UUID,
    store: Annotated[RepositoryStore, Depends(repository_store)],
    prs: Annotated[PullRequestStore, Depends(pull_request_store)],
    pagination: Annotated[PageParams, Depends()],
    status: PullRequestStatus | None = None,
) -> Page[PullRequestResponse]:
    if await store.get(repository_id) is None:
        raise HTTPException(404, "Repository not found.")
    return await prs.list(pagination, repository_id=repository_id, status=status)
