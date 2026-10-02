from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.read_dependencies import commit_store
from app.repositories.commit import CommitStore
from app.schemas.commit import CommitResponse
from app.schemas.pagination import Page, PageParams

router = APIRouter(prefix="/commits", tags=["commits"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=Page[CommitResponse])
async def list_commits(store: Annotated[CommitStore, Depends(commit_store)], pagination: Annotated[PageParams, Depends()], repository_id: UUID | None = None) -> Page[CommitResponse]:
    return await store.list(pagination, repository_id)