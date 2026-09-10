from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PullRequest, PullRequestStatus, Repository
from app.schemas.github import GitHubRepository
from app.schemas.pagination import Page, PageParams, paginated
from app.schemas.repository import RepositoryResponse


class RepositoryStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, data: GitHubRepository, synced_at: datetime) -> tuple[Repository, bool]:
        values = data.model_dump()
        result = await self.session.execute(
            insert(Repository).values(**values, last_synced_at=synced_at)
            .on_conflict_do_nothing(index_elements=[Repository.github_repository_id])
            .returning(Repository)
        )
        record = result.scalar_one_or_none()
        if record is not None:
            return record, True
        record = (await self.session.execute(
            select(Repository).where(Repository.github_repository_id == data.github_repository_id).with_for_update()
        )).scalar_one()
        if record.github_updated_at is None or data.github_updated_at >= record.github_updated_at:
            for key, value in values.items():
                setattr(record, key, value)
        # Installation ID and local active/inactive preference are intentionally preserved.
        record.last_synced_at = synced_at
        await self.session.flush()
        return record, False

    @staticmethod
    def _statement() -> Select[tuple[Repository, int, int]]:
        counts = select(
            PullRequest.repository_id,
            func.count().label("pr_count"),
            func.count().filter(PullRequest.status == PullRequestStatus.OPEN).label("open_count"),
        ).group_by(PullRequest.repository_id).subquery()
        return select(Repository, func.coalesce(counts.c.pr_count, 0), func.coalesce(counts.c.open_count, 0)).outerjoin(counts, Repository.id == counts.c.repository_id)

    @staticmethod
    def _response(record: Repository, total: int, open_count: int) -> RepositoryResponse:
        return RepositoryResponse.model_validate(record).model_copy(update={"pull_request_count": total, "open_pull_request_count": open_count})

    async def get(self, repository_id: UUID) -> RepositoryResponse | None:
        row = (await self.session.execute(self._statement().where(Repository.id == repository_id))).one_or_none()
        return self._response(*row) if row else None

    async def list(self, params: PageParams, search: str | None = None, is_active: bool | None = None) -> Page[RepositoryResponse]:
        filters = []
        if search:
            filters.append(Repository.full_name.icontains(search, autoescape=True))
        if is_active is not None:
            filters.append(Repository.is_active == is_active)
        total = (await self.session.execute(select(func.count()).select_from(Repository).where(*filters))).scalar_one()
        statement = self._statement().where(*filters).order_by(
            func.coalesce(Repository.last_synced_at, Repository.updated_at).desc(), Repository.id
        ).offset((params.page - 1) * params.page_size).limit(params.page_size)
        rows = (await self.session.execute(statement)).all()
        return paginated([self._response(*row) for row in rows], total, params)
