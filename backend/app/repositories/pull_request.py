from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PullRequest, PullRequestStatus, Repository
from app.schemas.github import GitHubPullRequest
from app.schemas.pagination import Page, PageParams, paginated
from app.schemas.pull_request import PullRequestDetail, PullRequestResponse
from app.schemas.repository import RepositorySummary


class PullRequestStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, repository_id: UUID, data: GitHubPullRequest, synced_at: datetime) -> Literal["created", "updated", "unchanged"]:
        values = data.model_dump()
        result = await self.session.execute(
            insert(PullRequest).values(**values, repository_id=repository_id, last_synced_at=synced_at)
            .on_conflict_do_nothing(index_elements=[PullRequest.repository_id, PullRequest.github_pr_number])
            .returning(PullRequest.id)
        )
        if result.scalar_one_or_none() is not None:
            return "created"
        record = (await self.session.execute(select(PullRequest).where(
            PullRequest.repository_id == repository_id, PullRequest.github_pr_number == data.github_pr_number
        ).with_for_update())).scalar_one()
        changed = False
        if record.github_updated_at is None or data.github_updated_at >= record.github_updated_at:
            for key, value in values.items():
                if getattr(record, key) != value:
                    setattr(record, key, value)
                    changed = True
        record.last_synced_at = synced_at
        await self.session.flush()
        return "updated" if changed else "unchanged"

    @staticmethod
    def _response(pr: PullRequest, repository: Repository) -> PullRequestResponse:
        return PullRequestResponse.model_validate(pr).model_copy(update={"repository_full_name": repository.full_name})

    async def get(self, pull_request_id: UUID) -> PullRequestDetail | None:
        row = (await self.session.execute(select(PullRequest, Repository).join(Repository).where(PullRequest.id == pull_request_id))).one_or_none()
        if row is None:
            return None
        pr, repo = row
        return PullRequestDetail(**self._response(pr, repo).model_dump(), repository=RepositorySummary.model_validate(repo))

    async def list(self, params: PageParams, search: str | None = None, repository_id: UUID | None = None, status: PullRequestStatus | None = None) -> Page[PullRequestResponse]:
        filters = []
        if repository_id is not None:
            filters.append(PullRequest.repository_id == repository_id)
        if status is not None:
            filters.append(PullRequest.status == status)
        if search:
            filters.append(or_(PullRequest.title.icontains(search, autoescape=True), PullRequest.author_login.icontains(search, autoescape=True)))
        total = (await self.session.execute(select(func.count()).select_from(PullRequest).where(*filters))).scalar_one()
        rows = (await self.session.execute(select(PullRequest, Repository).join(Repository).where(*filters).order_by(
            PullRequest.github_updated_at.desc().nulls_last(), PullRequest.id
        ).offset((params.page - 1) * params.page_size).limit(params.page_size))).all()
        return paginated([self._response(*row) for row in rows], total, params)
