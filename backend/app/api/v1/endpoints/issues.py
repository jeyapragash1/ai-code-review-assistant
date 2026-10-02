from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.read_dependencies import issue_store
from app.repositories.issue import IssueStore
from app.schemas.issue import IssueResponse
from app.schemas.pagination import Page, PageParams

router = APIRouter(prefix="/issues", tags=["issues"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=Page[IssueResponse])
async def list_issues(
    store: Annotated[IssueStore, Depends(issue_store)],
    pagination: Annotated[PageParams, Depends()],
    repository_id: UUID | None = None,
    state: Annotated[str | None, Query(pattern="^(open|closed)$")] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
    author: Annotated[str | None, Query(max_length=255)] = None,
    assignee: Annotated[str | None, Query(max_length=255)] = None,
    label: Annotated[str | None, Query(max_length=255)] = None,
) -> Page[IssueResponse]:
    return await store.list(pagination, repository_id, state, search, author, assignee, label)


@router.get("/{issue_id}", response_model=IssueResponse)
async def issue_detail(issue_id: UUID, store: Annotated[IssueStore, Depends(issue_store)]) -> IssueResponse:
    issue = await store.get(issue_id)
    if issue is None:
        raise HTTPException(404, "Issue not found.")
    return issue