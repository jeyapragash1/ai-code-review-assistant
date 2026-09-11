from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.read_dependencies import review_finding_store, review_store
from app.models.enums import FindingCategory, FindingSeverity, FindingSource, FindingStatus, ReviewRisk, ReviewStatus
from app.repositories.review import ReviewFindingStore, ReviewStore
from app.schemas.pagination import Page, PageParams
from app.schemas.review import ReviewDetail, ReviewFindingResponse, ReviewResponse
from app.api.v1.auth_dependencies import get_current_user

router = APIRouter(tags=["reviews"], dependencies=[Depends(get_current_user)])


@router.get("/reviews", response_model=Page[ReviewResponse])
async def list_reviews(
    store: Annotated[ReviewStore, Depends(review_store)],
    pagination: Annotated[PageParams, Depends()],
    pull_request_id: UUID | None = None,
    repository_id: UUID | None = None,
    status: ReviewStatus | None = None,
    overall_risk: ReviewRisk | None = None,
    commit_sha: Annotated[str | None, Query(min_length=7, max_length=40)] = None,
) -> Page[ReviewResponse]:
    return await store.list(pagination, pull_request_id, repository_id, status, overall_risk, commit_sha)


@router.get("/reviews/{review_id}", response_model=ReviewDetail)
async def review_detail(review_id: UUID, store: Annotated[ReviewStore, Depends(review_store)]) -> ReviewDetail:
    record = await store.get(review_id)
    if record is None:
        raise HTTPException(404, "Review not found.")
    return record


@router.get("/reviews/{review_id}/findings", response_model=Page[ReviewFindingResponse])
async def review_findings(
    review_id: UUID,
    reviews: Annotated[ReviewStore, Depends(review_store)],
    findings: Annotated[ReviewFindingStore, Depends(review_finding_store)],
    pagination: Annotated[PageParams, Depends()],
    severity: FindingSeverity | None = None,
    category: FindingCategory | None = None,
    status: FindingStatus | None = None,
    source: FindingSource | None = None,
    file_path: Annotated[str | None, Query(min_length=1, max_length=1024)] = None,
) -> Page[ReviewFindingResponse]:
    if await reviews.get(review_id) is None:
        raise HTTPException(404, "Review not found.")
    return await findings.list(pagination, review_id, severity, category, status, source, file_path)


@router.get("/review-findings/{finding_id}", response_model=ReviewFindingResponse)
async def finding_detail(
    finding_id: UUID,
    store: Annotated[ReviewFindingStore, Depends(review_finding_store)],
) -> ReviewFindingResponse:
    record = await store.get(finding_id)
    if record is None:
        raise HTTPException(404, "Review finding not found.")
    return record
