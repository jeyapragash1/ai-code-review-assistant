from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    FindingCategory,
    FindingSeverity,
    FindingSource,
    FindingStatus,
    PullRequest,
    Repository,
    Review,
    ReviewFinding,
    ReviewRisk,
    ReviewStatus,
)
from app.schemas.pagination import Page, PageParams, paginated
from app.schemas.pull_request import PullRequestDetail, PullRequestResponse
from app.schemas.repository import RepositorySummary
from app.schemas.review import ReviewCreate, ReviewDetail, ReviewFindingCreate, ReviewFindingResponse, ReviewResponse, ReviewStatusUpdate


class ReviewStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _counts_subquery():
        return select(
            ReviewFinding.review_id,
            func.count(ReviewFinding.id).label("findings_count"),
            func.count().filter(ReviewFinding.severity == FindingSeverity.HIGH).label("high_count"),
        ).group_by(ReviewFinding.review_id).subquery()

    @classmethod
    def _statement(cls) -> Select[tuple[Review, int, int]]:
        counts = cls._counts_subquery()
        return select(
            Review,
            func.coalesce(counts.c.findings_count, 0),
            func.coalesce(counts.c.high_count, 0),
        ).outerjoin(counts, Review.id == counts.c.review_id)

    @staticmethod
    def _response(record: Review, findings_count: int, high_count: int) -> ReviewResponse:
        return ReviewResponse.model_validate(record).model_copy(
            update={
                "findings_count": findings_count,
                "high_severity_findings_count": high_count,
            }
        )

    async def pull_request_exists(self, pull_request_id: UUID) -> bool:
        return (await self.session.execute(select(PullRequest.id).where(PullRequest.id == pull_request_id))).scalar_one_or_none() is not None

    async def get(self, review_id: UUID) -> ReviewDetail | None:
        counts = self._counts_subquery()
        row = (await self.session.execute(
            select(
                Review,
                PullRequest,
                Repository,
                func.coalesce(counts.c.findings_count, 0),
                func.coalesce(counts.c.high_count, 0),
            )
            .join(PullRequest, Review.pull_request_id == PullRequest.id)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .outerjoin(counts, Review.id == counts.c.review_id)
            .where(Review.id == review_id)
        )).one_or_none()
        if row is None:
            return None
        review, pull_request, repository, findings_count, high_count = row
        review_response = self._response(review, findings_count, high_count)
        pull_request_response = PullRequestResponse.model_validate(pull_request).model_copy(
            update={"repository_full_name": repository.full_name}
        )
        pull_request_detail = PullRequestDetail(
            **pull_request_response.model_dump(),
            repository=RepositorySummary.model_validate(repository),
        )
        return ReviewDetail(**review_response.model_dump(), pull_request=pull_request_detail)

    async def list(
        self,
        params: PageParams,
        pull_request_id: UUID | None = None,
        repository_id: UUID | None = None,
        status: ReviewStatus | None = None,
        overall_risk: ReviewRisk | None = None,
        commit_sha: str | None = None,
    ) -> Page[ReviewResponse]:
        filters = []
        join_pull_requests = repository_id is not None
        if pull_request_id is not None:
            filters.append(Review.pull_request_id == pull_request_id)
        if repository_id is not None:
            filters.append(PullRequest.repository_id == repository_id)
        if status is not None:
            filters.append(Review.status == status)
        if overall_risk is not None:
            filters.append(Review.overall_risk == overall_risk)
        if commit_sha is not None:
            filters.append(Review.commit_sha == commit_sha)

        count_statement = select(func.count()).select_from(Review)
        statement = self._statement()
        if join_pull_requests:
            count_statement = count_statement.join(PullRequest, Review.pull_request_id == PullRequest.id)
            statement = statement.join(PullRequest, Review.pull_request_id == PullRequest.id)

        total = (await self.session.execute(count_statement.where(*filters))).scalar_one()
        rows = (await self.session.execute(
            statement.where(*filters)
            .order_by(Review.started_at.desc(), Review.id)
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
        )).all()
        return paginated([self._response(*row) for row in rows], total, params)

    async def create(self, data: ReviewCreate) -> Review:
        values = data.model_dump(exclude_none=True)
        record = Review(**values)
        self.session.add(record)
        await self.session.flush()
        return record

    async def mark_status(self, review_id: UUID, data: ReviewStatusUpdate) -> Review | None:
        record = (await self.session.execute(select(Review).where(Review.id == review_id).with_for_update())).scalar_one_or_none()
        if record is None:
            return None
        updates = data.model_dump(exclude_unset=True)
        if data.status in {ReviewStatus.COMPLETED, ReviewStatus.FAILED} and updates.get("completed_at") is None:
            updates["completed_at"] = datetime.now(UTC)
        for key, value in updates.items():
            setattr(record, key, value)
        await self.session.flush()
        return record


class ReviewFindingStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def review_exists(self, review_id: UUID) -> bool:
        return (await self.session.execute(select(Review.id).where(Review.id == review_id))).scalar_one_or_none() is not None

    async def get(self, finding_id: UUID) -> ReviewFindingResponse | None:
        record = (await self.session.execute(select(ReviewFinding).where(ReviewFinding.id == finding_id))).scalar_one_or_none()
        return ReviewFindingResponse.model_validate(record) if record else None

    async def list(
        self,
        params: PageParams,
        review_id: UUID | None = None,
        severity: FindingSeverity | None = None,
        category: FindingCategory | None = None,
        status: FindingStatus | None = None,
        source: FindingSource | None = None,
        file_path: str | None = None,
    ) -> Page[ReviewFindingResponse]:
        filters = []
        if review_id is not None:
            filters.append(ReviewFinding.review_id == review_id)
        if severity is not None:
            filters.append(ReviewFinding.severity == severity)
        if category is not None:
            filters.append(ReviewFinding.category == category)
        if status is not None:
            filters.append(ReviewFinding.status == status)
        if source is not None:
            filters.append(ReviewFinding.source == source)
        if file_path:
            filters.append(ReviewFinding.file_path.icontains(file_path, autoescape=True))

        total = (await self.session.execute(select(func.count()).select_from(ReviewFinding).where(*filters))).scalar_one()
        rows = (await self.session.execute(
            select(ReviewFinding)
            .where(*filters)
            .order_by(ReviewFinding.created_at.desc(), ReviewFinding.id)
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
        )).scalars().all()
        return paginated([ReviewFindingResponse.model_validate(record) for record in rows], total, params)

    async def create_idempotent(self, findings: list[ReviewFindingCreate]) -> int:
        created = 0
        for finding in findings:
            result = await self.session.execute(
                insert(ReviewFinding)
                .values(**finding.model_dump())
                .on_conflict_do_nothing(index_elements=[ReviewFinding.review_id, ReviewFinding.fingerprint])
                .returning(ReviewFinding.id)
            )
            if result.scalar_one_or_none() is not None:
                created += 1
        await self.session.flush()
        return created
